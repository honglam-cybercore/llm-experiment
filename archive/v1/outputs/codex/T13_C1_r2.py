import ipaddress
from urllib.parse import urlsplit


class URLValidator:
    def __init__(self, allowed_schemes, allowed_hosts, allowed_ports, blocked_networks) -> None:
        self._allowed_schemes = {
            scheme.lower() for scheme in allowed_schemes if isinstance(scheme, str)
        }
        self._allowed_hosts = {
            host.rstrip(".").lower()
            for host in allowed_hosts
            if isinstance(host, str)
        }
        self._allowed_ports = {
            port for port in allowed_ports
            if isinstance(port, int) and not isinstance(port, bool)
        }

        networks = []
        for network in blocked_networks:
            if isinstance(network, str):
                try:
                    networks.append(ipaddress.ip_network(network, strict=False))
                except ValueError:
                    pass
        self._blocked_networks = tuple(networks)

    def validate(self, url) -> bool:
        if not isinstance(url, str) or not url or any(
            ord(char) < 32 or ord(char) == 127 or char.isspace()
            for char in url
        ):
            return False

        try:
            parsed = urlsplit(url)
            if not parsed.scheme or not parsed.netloc:
                return False

            scheme = parsed.scheme.lower()
            if scheme not in self._allowed_schemes:
                return False

            hostname = parsed.hostname
            if not hostname:
                return False

            normalized_host = hostname.rstrip(".").lower()
            if normalized_host not in self._allowed_hosts:
                return False

            try:
                port = parsed.port
            except ValueError:
                return False

            if parsed.netloc.rsplit("@", 1)[-1].endswith(":"):
                return False

            if port is not None and port not in self._allowed_ports:
                return False

            try:
                address = ipaddress.ip_address(hostname)
            except ValueError:
                address = None

            if address is not None and any(
                address in network for network in self._blocked_networks
            ):
                return False

            return True
        except (TypeError, ValueError):
            return False