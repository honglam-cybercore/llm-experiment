import ipaddress
from urllib.parse import urlsplit


class URLValidator:
    def __init__(self, allowed_schemes, allowed_hosts, allowed_ports, blocked_networks) -> None:
        self._configuration_valid = True

        try:
            self._allowed_schemes = {
                value.casefold()
                for value in allowed_schemes
                if isinstance(value, str)
            }
        except (TypeError, AttributeError):
            self._allowed_schemes = set()
            self._configuration_valid = False

        try:
            self._allowed_hosts = {
                value.casefold()
                for value in allowed_hosts
                if isinstance(value, str)
            }
        except (TypeError, AttributeError):
            self._allowed_hosts = set()
            self._configuration_valid = False

        try:
            self._allowed_ports = {
                value
                for value in allowed_ports
                if type(value) is int and 0 <= value <= 65535
            }
        except TypeError:
            self._allowed_ports = set()
            self._configuration_valid = False

        self._blocked_networks = []
        try:
            for network in blocked_networks:
                if not isinstance(network, str):
                    self._configuration_valid = False
                    continue
                self._blocked_networks.append(
                    ipaddress.ip_network(network, strict=False)
                )
        except (TypeError, ValueError):
            self._configuration_valid = False

    def validate(self, url) -> bool:
        if not self._configuration_valid or not isinstance(url, str) or not url:
            return False

        if url != url.strip():
            return False

        if any(ord(char) < 32 or ord(char) == 127 for char in url):
            return False

        try:
            parsed = urlsplit(url)
            scheme = parsed.scheme.casefold()

            if scheme not in self._allowed_schemes:
                return False

            if not parsed.netloc or "@" in parsed.netloc:
                return False

            hostname = parsed.hostname
            if not hostname:
                return False

            hostname_key = hostname.casefold()
            if hostname_key not in self._allowed_hosts:
                return False

            if hostname_key.rstrip(".") == "localhost":
                return False

            if "%" in hostname or any(char.isspace() for char in hostname):
                return False

            if parsed.netloc.startswith("["):
                closing_bracket = parsed.netloc.find("]")
                if closing_bracket < 0:
                    return False
                suffix = parsed.netloc[closing_bracket + 1:]
                if suffix and not suffix.startswith(":"):
                    return False
                if suffix == ":":
                    return False
            elif parsed.netloc.count(":") > 1:
                return False
            elif ":" in parsed.netloc and parsed.netloc.endswith(":"):
                return False

            port = parsed.port
            explicit_port = False

            if parsed.netloc.startswith("["):
                closing_bracket = parsed.netloc.find("]")
                explicit_port = (
                    closing_bracket >= 0
                    and len(parsed.netloc) > closing_bracket + 1
                )
            else:
                explicit_port = ":" in parsed.netloc

            if explicit_port and port not in self._allowed_ports:
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

                if any(
                    address.version == network.version and address in network
                    for network in self._blocked_networks
                ):
                    return False

            return True

        except (TypeError, ValueError, UnicodeError):
            return False