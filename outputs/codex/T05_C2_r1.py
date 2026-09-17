from urllib.parse import urlsplit
import ipaddress


class URLValidator:
    def __init__(self, allowed_schemes, allowed_hosts, allowed_ports, blocked_networks) -> None:
        self._configuration_valid = True
        self._schemes = set()
        self._hosts = set()
        self._ports = set()
        self._networks = []

        try:
            if not isinstance(allowed_schemes, list):
                raise ValueError
            if not isinstance(allowed_hosts, list):
                raise ValueError
            if not isinstance(allowed_ports, list):
                raise ValueError
            if not isinstance(blocked_networks, list):
                raise ValueError

            if not all(isinstance(value, str) for value in allowed_schemes):
                raise ValueError
            if not all(isinstance(value, str) for value in allowed_hosts):
                raise ValueError
            if not all(isinstance(value, int) and not isinstance(value, bool)
                       for value in allowed_ports):
                raise ValueError
            if not all(isinstance(value, str) for value in blocked_networks):
                raise ValueError

            self._schemes = {value.lower() for value in allowed_schemes}
            self._hosts = {
                value[1:-1].lower() if value.startswith("[") and value.endswith("]")
                else value.lower()
                for value in allowed_hosts
            }
            self._ports = set(allowed_ports)
            self._networks = [
                ipaddress.ip_network(value, strict=False)
                for value in blocked_networks
            ]
        except (TypeError, ValueError):
            self._configuration_valid = False

    def validate(self, url) -> bool:
        if not self._configuration_valid or not isinstance(url, str) or not url:
            return False

        if any(character.isspace() or ord(character) < 32 for character in url):
            return False

        try:
            parsed = urlsplit(url)
            scheme = parsed.scheme.lower()

            if scheme not in self._schemes or not parsed.netloc:
                return False

            if "@" in parsed.netloc:
                return False

            hostname = parsed.hostname
            if not hostname:
                return False

            hostname = hostname.lower()

            if "%" in hostname or hostname == "localhost":
                return False

            if hostname not in self._hosts:
                return False

            if parsed.netloc.startswith("["):
                closing_bracket = parsed.netloc.find("]")
                if closing_bracket < 0:
                    return False
                suffix = parsed.netloc[closing_bracket + 1:]
                explicit_port = bool(suffix)
                if explicit_port and not suffix.startswith(":"):
                    return False
            else:
                colon_count = parsed.netloc.count(":")
                if colon_count > 1:
                    return False
                explicit_port = colon_count == 1

            if explicit_port:
                port = parsed.port
                if port is None or port not in self._ports:
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
                ):
                    return False

                for network in self._networks:
                    candidate = address
                    if (
                        isinstance(address, ipaddress.IPv6Address)
                        and address.ipv4_mapped is not None
                        and isinstance(network, ipaddress.IPv4Network)
                    ):
                        candidate = address.ipv4_mapped
                    if candidate in network:
                        return False

            return True
        except (TypeError, ValueError, IndexError):
            return False