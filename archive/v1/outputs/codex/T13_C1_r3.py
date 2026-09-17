from ipaddress import ip_address, ip_network
from urllib.parse import urlsplit


class URLValidator:
    def __init__(self, allowed_schemes, allowed_hosts, allowed_ports, blocked_networks) -> None:
        self._allowed_schemes = {
            value.lower()
            for value in allowed_schemes
            if isinstance(value, str)
        }
        self._allowed_hosts = {
            value.strip("[]").lower()
            for value in allowed_hosts
            if isinstance(value, str)
        }
        self._allowed_ports = {
            value
            for value in allowed_ports
            if isinstance(value, int) and not isinstance(value, bool)
        }
        self._blocked_networks = []
        for network in blocked_networks:
            try:
                self._blocked_networks.append(ip_network(network, strict=False))
            except (ValueError, TypeError):
                continue

    def validate(self, url) -> bool:
        if not isinstance(url, str) or not url:
            return False

        if any(ord(char) <= 32 or ord(char) == 127 for char in url):
            return False

        for index, char in enumerate(url):
            if char == "%":
                if (
                    index + 2 >= len(url)
                    or url[index + 1] not in "0123456789abcdefABCDEF"
                    or url[index + 2] not in "0123456789abcdefABCDEF"
                ):
                    return False

        try:
            parsed = urlsplit(url)
            scheme = parsed.scheme.lower()
            hostname = parsed.hostname
            port = parsed.port
        except (ValueError, TypeError):
            return False

        if not scheme or scheme not in self._allowed_schemes:
            return False

        if not parsed.netloc or not hostname:
            return False

        hostname = hostname.lower()

        if hostname not in self._allowed_hosts:
            return False

        try:
            address = ip_address(hostname)
        except ValueError:
            address = None

        if address is not None and any(
            address.version == network.version and address in network
            for network in self._blocked_networks
        ):
            return False

        authority = parsed.netloc.rsplit("@", 1)[-1]
        if authority.startswith("["):
            closing_bracket = authority.find("]")
            if closing_bracket < 0:
                return False
            suffix = authority[closing_bracket + 1:]
            explicit_port = suffix.startswith(":")
            if explicit_port and len(suffix) == 1:
                return False
        else:
            explicit_port = ":" in authority

        if explicit_port and port not in self._allowed_ports:
            return False

        return True