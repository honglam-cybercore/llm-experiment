import ipaddress
from urllib.parse import urlsplit


class URLValidator:
    def __init__(self, allowed_schemes, allowed_hosts, allowed_ports, blocked_networks) -> None:
        self._configuration_valid = True

        try:
            if not isinstance(allowed_schemes, (list, tuple, set)):
                raise ValueError
            self._allowed_schemes = {
                value.lower() for value in allowed_schemes
                if isinstance(value, str)
            }
            if len(self._allowed_schemes) != len(allowed_schemes):
                raise ValueError
        except (TypeError, ValueError):
            self._configuration_valid = False
            self._allowed_schemes = set()

        try:
            if not isinstance(allowed_hosts, (list, tuple, set)):
                raise ValueError

            normalized_hosts = set()
            for host in allowed_hosts:
                if not isinstance(host, str) or not host:
                    raise ValueError
                if host.startswith("[") and host.endswith("]"):
                    host = host[1:-1]
                normalized_hosts.add(host.lower())

            if len(normalized_hosts) != len(allowed_hosts):
                raise ValueError
            self._allowed_hosts = normalized_hosts
        except (TypeError, ValueError):
            self._configuration_valid = False
            self._allowed_hosts = set()

        try:
            if not isinstance(allowed_ports, (list, tuple, set)):
                raise ValueError

            ports = set()
            for port in allowed_ports:
                if isinstance(port, bool) or not isinstance(port, int):
                    raise ValueError
                if not 0 <= port <= 65535:
                    raise ValueError
                ports.add(port)

            self._allowed_ports = ports
        except (TypeError, ValueError):
            self._configuration_valid = False
            self._allowed_ports = set()

        try:
            if not isinstance(blocked_networks, (list, tuple, set)):
                raise ValueError

            networks = []
            for network in blocked_networks:
                if not isinstance(network, str):
                    raise ValueError
                networks.append(ipaddress.ip_network(network, strict=False))

            self._blocked_networks = tuple(networks)
        except (TypeError, ValueError):
            self._configuration_valid = False
            self._blocked_networks = ()

    def validate(self, url) -> bool:
        if not self._configuration_valid or not isinstance(url, str) or not url:
            return False

        if any(character.isspace() or ord(character) < 32 or ord(character) == 127
               for character in url):
            return False

        try:
            parsed = urlsplit(url)
            if not parsed.scheme or not parsed.netloc:
                return False

            if parsed.scheme.lower() not in self._allowed_schemes:
                return False

            if "@" in parsed.netloc:
                return False

            hostname = parsed.hostname
            if not hostname:
                return False

            hostname = hostname.lower()

            if (
                "\\" in hostname
                or "/" in hostname
                or ":" in hostname
                or "%" in hostname
            ):
                return False

            if hostname.rstrip(".") == "localhost":
                return False

            if hostname not in self._allowed_hosts:
                return False

            authority = parsed.netloc
            if authority.startswith("["):
                closing_bracket = authority.find("]")
                if closing_bracket < 0:
                    return False
                port_explicit = authority[closing_bracket + 1:].startswith(":")
            else:
                port_explicit = ":" in authority

            if port_explicit:
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
                ):
                    return False

                if any(address in network for network in self._blocked_networks):
                    return False

            return True
        except (TypeError, ValueError, UnicodeError):
            return False