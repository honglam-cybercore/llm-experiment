import ipaddress
from urllib.parse import urlsplit


class URLValidator:
    def __init__(self, allowed_schemes, allowed_hosts, allowed_ports, blocked_networks) -> None:
        self._allowed_schemes = {
            value.lower() for value in allowed_schemes if isinstance(value, str)
        }
        self._allowed_hosts = {
            self._normalize_host(value)
            for value in allowed_hosts
            if isinstance(value, str)
        }
        self._allowed_ports = {
            value for value in allowed_ports
            if isinstance(value, int) and not isinstance(value, bool)
        }

        self._blocked_networks = []
        for network in blocked_networks:
            if isinstance(network, str):
                try:
                    self._blocked_networks.append(
                        ipaddress.ip_network(network, strict=False)
                    )
                except ValueError:
                    continue

    @staticmethod
    def _normalize_host(host):
        host = host.strip().lower()
        if host.startswith("[") and host.endswith("]"):
            host = host[1:-1]
        if ":" not in host:
            host = host.rstrip(".")
        return host

    @staticmethod
    def _has_explicit_port(netloc):
        endpoint = netloc.rsplit("@", 1)[-1]
        if endpoint.startswith("["):
            closing = endpoint.find("]")
            return closing != -1 and endpoint[closing + 1:].startswith(":")
        return ":" in endpoint

    def validate(self, url) -> bool:
        if not isinstance(url, str) or not url:
            return False

        if any(ord(char) <= 32 for char in url):
            return False

        try:
            parsed = urlsplit(url)
            hostname = parsed.hostname
        except (ValueError, UnicodeError):
            return False

        if not parsed.scheme or not parsed.netloc or hostname is None:
            return False

        scheme = parsed.scheme.lower()
        host = self._normalize_host(hostname)

        if scheme not in self._allowed_schemes:
            return False

        if host not in self._allowed_hosts:
            return False

        try:
            port = parsed.port
        except ValueError:
            return False

        if self._has_explicit_port(parsed.netloc):
            if port is None or port not in self._allowed_ports:
                return False

        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            address = None

        if address is not None:
            for network in self._blocked_networks:
                if address.version == network.version and address in network:
                    return False

        return True