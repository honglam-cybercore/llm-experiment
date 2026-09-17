from ipaddress import ip_address, ip_network
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
                if host.startswith("[") and host.endswith("]"):
                    host = host[1:-1]
                self._allowed_hosts.add(host.casefold())

        self._allowed_ports = {
            value for value in allowed_ports
            if isinstance(value, int) and not isinstance(value, bool)
            and 0 <= value <= 65535
        }

        self._blocked_networks = []
        self._invalid_blocked_networks = False
        for value in blocked_networks:
            try:
                self._blocked_networks.append(ip_network(value, strict=False))
            except (TypeError, ValueError):
                self._invalid_blocked_networks = True

    def validate(self, url) -> bool:
        if not isinstance(url, str) or not url:
            return False

        if any(ord(char) <= 32 or ord(char) == 127 for char in url):
            return False

        try:
            parsed = urlsplit(url)
        except ValueError:
            return False

        if parsed.scheme.casefold() not in self._allowed_schemes:
            return False

        if not parsed.netloc or "@" in parsed.netloc:
            return False

        try:
            hostname = parsed.hostname
        except ValueError:
            return False

        if not hostname:
            return False

        host = hostname.casefold()
        if host == "localhost":
            return False

        if host not in self._allowed_hosts:
            return False

        netloc = parsed.netloc
        explicit_port = False

        if netloc.startswith("["):
            closing = netloc.find("]")
            if closing < 0:
                return False
            suffix = netloc[closing + 1:]
            if suffix:
                if not suffix.startswith(":") or len(suffix) == 1:
                    return False
                explicit_port = True
        else:
            if netloc.count(":") > 1:
                return False
            if ":" in netloc:
                port_text = netloc.rsplit(":", 1)[1]
                if not port_text.isdigit():
                    return False
                explicit_port = True

        try:
            port = parsed.port
        except ValueError:
            return False

        if explicit_port:
            if port is None or port not in self._allowed_ports:
                return False

        try:
            address = ip_address(host)
        except ValueError:
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

        if self._invalid_blocked_networks:
            return False

        return True