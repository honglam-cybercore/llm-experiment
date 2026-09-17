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
            normalized = self._normalize_host(value)
            if normalized is not None:
                self._allowed_hosts.add(normalized)

        self._allowed_ports = {
            value
            for value in allowed_ports
            if isinstance(value, int) and not isinstance(value, bool)
            and 1 <= value <= 65535
        }

        self._blocked_networks = []
        for value in blocked_networks:
            if not isinstance(value, str):
                continue
            try:
                self._blocked_networks.append(
                    ipaddress.ip_network(value, strict=False)
                )
            except (ValueError, TypeError):
                continue

    @staticmethod
    def _normalize_host(host):
        if not isinstance(host, str) or not host:
            return None

        if any(character.isspace() or ord(character) < 32 for character in host):
            return None

        if host.startswith("[") and host.endswith("]"):
            host = host[1:-1]
        elif host.startswith("[") or host.endswith("]"):
            return None

        try:
            address = ipaddress.ip_address(host)
            return address.compressed.casefold()
        except ValueError:
            pass

        try:
            return host.encode("idna").decode("ascii").casefold()
        except (UnicodeError, ValueError):
            return None

    def _is_blocked_ip(self, address):
        if (
            address.is_loopback
            or address.is_private
            or address.is_link_local
            or address.is_unspecified
            or address.is_reserved
            or address.is_multicast
        ):
            return True

        return any(address in network for network in self._blocked_networks)

    def validate(self, url) -> bool:
        if not isinstance(url, str) or not url or url != url.strip():
            return False

        try:
            parsed = urlsplit(url)

            if (
                not parsed.scheme
                or not parsed.netloc
                or parsed.scheme.casefold() not in self._allowed_schemes
                or parsed.username is not None
                or parsed.password is not None
            ):
                return False

            hostname = parsed.hostname
            normalized_host = self._normalize_host(hostname)
            if normalized_host is None:
                return False

            if normalized_host == "localhost":
                return False

            if normalized_host not in self._allowed_hosts:
                return False

            try:
                address = ipaddress.ip_address(hostname)
            except (ValueError, TypeError):
                address = None

            if address is not None and self._is_blocked_ip(address):
                return False

            if parsed.port is not None and parsed.port not in self._allowed_ports:
                return False

            return True
        except (ValueError, TypeError, UnicodeError, AttributeError):
            return False
