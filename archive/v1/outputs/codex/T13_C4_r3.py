import ipaddress
from urllib.parse import urlsplit


class URLValidator:
    def __init__(self, allowed_schemes, allowed_hosts, allowed_ports, blocked_networks) -> None:
        self._allowed_schemes = frozenset(
            value.casefold()
            for value in allowed_schemes
            if isinstance(value, str)
        )
        self._allowed_hosts = frozenset(
            value.casefold()
            for value in allowed_hosts
            if isinstance(value, str)
        )
        self._allowed_ports = frozenset(
            value
            for value in allowed_ports
            if isinstance(value, int) and not isinstance(value, bool)
            and 0 <= value <= 65535
        )

        networks = []
        for value in blocked_networks:
            if not isinstance(value, str):
                continue
            try:
                networks.append(ipaddress.ip_network(value, strict=False))
            except (ValueError, TypeError):
                continue
        self._blocked_networks = tuple(networks)

    def validate(self, url) -> bool:
        if not isinstance(url, str) or not url:
            return False

        if any(character.isspace() or ord(character) < 32 or ord(character) == 127
               for character in url):
            return False

        try:
            parsed = urlsplit(url)

            if parsed.scheme.casefold() not in self._allowed_schemes:
                return False

            if not parsed.netloc or "@" in parsed.netloc:
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
                    if authority.endswith(":"):
                        return False
                    explicit_port = True

            hostname = parsed.hostname
            if not hostname:
                return False

            hostname = hostname.casefold()

            if (
                "\\" in hostname
                or any(character.isspace() for character in hostname)
                or hostname in {"localhost", "localhost."}
            ):
                return False

            if hostname not in self._allowed_hosts:
                return False

            if explicit_port:
                try:
                    port = parsed.port
                except ValueError:
                    return False
                if port is None or port not in self._allowed_ports:
                    return False

            if "%" in hostname:
                return False

            try:
                address = ipaddress.ip_address(hostname)
            except ValueError:
                return True

            if address.is_loopback or address.is_private or address.is_link_local:
                return False

            for network in self._blocked_networks:
                if address.version == network.version and address in network:
                    return False

                mapped = getattr(address, "ipv4_mapped", None)
                if mapped is not None and network.version == 4 and mapped in network:
                    return False

            return True

        except (ValueError, TypeError, UnicodeError):
            return False
