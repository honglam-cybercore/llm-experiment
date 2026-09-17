import ipaddress
from urllib.parse import urlsplit


class URLValidator:
    def __init__(self, allowed_schemes, allowed_hosts, allowed_ports, blocked_networks) -> None:
        self._allowed_schemes = {
            value.casefold()
            for value in allowed_schemes
            if isinstance(value, str)
        }

        self._allowed_hosts = set()
        for value in allowed_hosts:
            if isinstance(value, str):
                host = value
                if len(host) >= 2 and host.startswith("[") and host.endswith("]"):
                    host = host[1:-1]
                self._allowed_hosts.add(host.casefold())

        self._allowed_ports = {
            value
            for value in allowed_ports
            if isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 65535
        }

        self._blocked_networks = []
        for value in blocked_networks:
            if isinstance(value, str):
                try:
                    self._blocked_networks.append(ipaddress.ip_network(value, strict=False))
                except (ValueError, TypeError):
                    pass

    def validate(self, url) -> bool:
        if not isinstance(url, str) or not url:
            return False

        if any(character.isspace() or ord(character) < 32 or ord(character) == 127
               for character in url):
            return False

        try:
            parsed = urlsplit(url)
        except (ValueError, TypeError):
            return False

        if not parsed.scheme or parsed.scheme.casefold() not in self._allowed_schemes:
            return False

        if not parsed.netloc or "@" in parsed.netloc:
            return False

        try:
            hostname = parsed.hostname
            port = parsed.port
        except (ValueError, TypeError):
            return False

        if not hostname:
            return False

        normalized_host = hostname.casefold()
        if normalized_host not in self._allowed_hosts:
            return False

        if normalized_host == "localhost":
            return False

        if parsed.netloc.endswith(":"):
            return False

        if port is not None and port not in self._allowed_ports:
            return False

        try:
            address = ipaddress.ip_address(hostname)
        except (ValueError, TypeError):
            address = None

        if address is not None:
            if (
                address.is_loopback
                or address.is_private
                or address.is_link_local
                or address.is_unspecified
            ):
                return False

            for network in self._blocked_networks:
                if address.version == network.version and address in network:
                    return False

        return True
