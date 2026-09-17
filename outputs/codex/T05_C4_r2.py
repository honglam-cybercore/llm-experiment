import ipaddress
from urllib.parse import urlsplit


class URLValidator:
    def __init__(self, allowed_schemes, allowed_hosts, allowed_ports, blocked_networks) -> None:
        self._allowed_schemes = {
            value.lower()
            for value in allowed_schemes
            if isinstance(value, str)
        }

        self._allowed_hosts = set()
        for value in allowed_hosts:
            if not isinstance(value, str):
                continue
            host = value
            if len(host) >= 2 and host.startswith("[") and host.endswith("]"):
                host = host[1:-1]
            self._allowed_hosts.add(host.lower())

        self._allowed_ports = {
            value
            for value in allowed_ports
            if isinstance(value, int) and not isinstance(value, bool)
            and 0 <= value <= 65535
        }

        self._blocked_networks = []
        for value in blocked_networks:
            if not isinstance(value, str):
                continue
            try:
                self._blocked_networks.append(
                    ipaddress.ip_network(value, strict=False)
                )
            except ValueError:
                continue

    def validate(self, url) -> bool:
        if not isinstance(url, str) or not url:
            return False

        if any(ord(char) <= 0x20 or ord(char) == 0x7F for char in url):
            return False

        try:
            parsed = urlsplit(url)
            if not parsed.scheme or parsed.scheme.lower() not in self._allowed_schemes:
                return False

            if not parsed.netloc or "@" in parsed.netloc or "\\" in parsed.netloc:
                return False

            hostname = parsed.hostname
            if not hostname:
                return False

            hostname = hostname.lower()
            if hostname == "localhost":
                return False

            if hostname not in self._allowed_hosts:
                return False

            if "%" in hostname:
                return False

            authority = parsed.netloc
            explicit_port = False
            port = None

            if authority.startswith("["):
                closing = authority.find("]")
                if closing < 0:
                    return False
                remainder = authority[closing + 1:]
                if remainder:
                    if not remainder.startswith(":") or len(remainder) == 1:
                        return False
                    explicit_port = True
                    port_text = remainder[1:]
                    if not port_text.isdigit():
                        return False
                    port = parsed.port
            else:
                if "[" in authority or "]" in authority:
                    return False
                colon_count = authority.count(":")
                if colon_count > 1:
                    return False
                if colon_count == 1:
                    explicit_port = True
                    _, port_text = authority.rsplit(":", 1)
                    if not port_text or not port_text.isdigit():
                        return False
                    port = parsed.port

            if explicit_port and port not in self._allowed_ports:
                return False

            try:
                address = ipaddress.ip_address(hostname)
            except ValueError:
                return True

            if (
                address.is_loopback
                or address.is_private
                or address.is_link_local
                or address.is_unspecified
            ):
                return False

            addresses = [address]
            if address.version == 6 and address.ipv4_mapped is not None:
                addresses.append(address.ipv4_mapped)

            for candidate in addresses:
                if any(
                    candidate.version == network.version
                    and candidate in network
                    for network in self._blocked_networks
                ):
                    return False

            return True
        except (ValueError, TypeError, UnicodeError):
            return False