import ipaddress
from urllib.parse import urlsplit


class URLValidator:
    def __init__(self, allowed_schemes, allowed_hosts, allowed_ports, blocked_networks) -> None:
        self._config_valid = True
        self._allowed_schemes = set()
        self._allowed_hosts = set()
        self._allowed_ports = set()
        self._blocked_networks = []

        try:
            if not isinstance(allowed_schemes, list):
                raise ValueError
            if not isinstance(allowed_hosts, list):
                raise ValueError
            if not isinstance(allowed_ports, list):
                raise ValueError
            if not isinstance(blocked_networks, list):
                raise ValueError

            for scheme in allowed_schemes:
                if not isinstance(scheme, str) or not scheme:
                    raise ValueError
                self._allowed_schemes.add(scheme.casefold())

            for host in allowed_hosts:
                if not isinstance(host, str) or not host:
                    raise ValueError
                self._allowed_hosts.add(host.casefold())

            for port in allowed_ports:
                if isinstance(port, bool) or not isinstance(port, int):
                    raise ValueError
                if not 0 <= port <= 65535:
                    raise ValueError
                self._allowed_ports.add(port)

            for network in blocked_networks:
                if not isinstance(network, str) or not network:
                    raise ValueError
                self._blocked_networks.append(ipaddress.ip_network(network, strict=False))
        except (TypeError, ValueError):
            self._config_valid = False

    def validate(self, url) -> bool:
        if not self._config_valid or not isinstance(url, str) or not url:
            return False

        if any(ord(char) < 32 or ord(char) == 127 or char.isspace() for char in url):
            return False

        try:
            parsed = urlsplit(url)
            scheme = parsed.scheme.casefold()

            if scheme not in self._allowed_schemes:
                return False
            if not parsed.netloc or "@" in parsed.netloc:
                return False
            if "\\" in parsed.netloc or "%" in parsed.netloc:
                return False

            authority = parsed.netloc
            explicit_port = False

            if authority.startswith("["):
                closing = authority.find("]")
                if closing < 0:
                    return False
                suffix = authority[closing + 1:]
                if suffix:
                    if not suffix.startswith(":") or len(suffix) == 1:
                        return False
                    explicit_port = True
            else:
                colon_count = authority.count(":")
                if colon_count > 1:
                    return False
                if colon_count == 1:
                    if authority.rsplit(":", 1)[1] == "":
                        return False
                    explicit_port = True

            hostname = parsed.hostname
            if hostname is None:
                return False

            hostname = hostname.casefold()
            if hostname not in self._allowed_hosts:
                return False

            if hostname == "localhost" or hostname.rstrip(".") == "localhost":
                return False

            if explicit_port:
                port = parsed.port
                if port is None or port not in self._allowed_ports:
                    return False

            try:
                address = ipaddress.ip_address(hostname)
            except ValueError:
                address = None

            if address is not None:
                if (
                    address.is_loopback
                    or address.is_private
                    or address.is_link_local
                    or address.is_unspecified
                    or address.is_reserved
                    or address.is_multicast
                ):
                    return False

                if any(address in network for network in self._blocked_networks):
                    return False

            return True
        except (TypeError, ValueError):
            return False