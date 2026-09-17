import ipaddress
from urllib.parse import urlsplit


class URLValidator:
    def __init__(self, allowed_schemes, allowed_hosts, allowed_ports, blocked_networks) -> None:
        self._configuration_valid = True

        if not isinstance(allowed_schemes, list):
            self._configuration_valid = False
            allowed_schemes = []
        if not isinstance(allowed_hosts, list):
            self._configuration_valid = False
            allowed_hosts = []
        if not isinstance(allowed_ports, list):
            self._configuration_valid = False
            allowed_ports = []
        if not isinstance(blocked_networks, list):
            self._configuration_valid = False
            blocked_networks = []

        self._allowed_schemes = set()
        for scheme in allowed_schemes:
            if not isinstance(scheme, str) or not scheme:
                self._configuration_valid = False
            else:
                self._allowed_schemes.add(scheme.casefold())

        self._allowed_hosts = set()
        for host in allowed_hosts:
            if not isinstance(host, str) or not host:
                self._configuration_valid = False
                continue
            normalized = host.casefold()
            if normalized.startswith("[") and normalized.endswith("]"):
                normalized = normalized[1:-1]
            self._allowed_hosts.add(normalized)

        self._allowed_ports = set()
        for port in allowed_ports:
            if isinstance(port, bool) or not isinstance(port, int) or not 0 <= port <= 65535:
                self._configuration_valid = False
            else:
                self._allowed_ports.add(port)

        self._blocked_networks = []
        for network in blocked_networks:
            if not isinstance(network, str):
                self._configuration_valid = False
                continue
            try:
                self._blocked_networks.append(ipaddress.ip_network(network, strict=False))
            except ValueError:
                self._configuration_valid = False

    def validate(self, url) -> bool:
        if not self._configuration_valid or not isinstance(url, str) or not url:
            return False

        if any(ord(char) <= 32 or ord(char) == 127 for char in url):
            return False

        try:
            parsed = urlsplit(url)
        except (TypeError, ValueError):
            return False

        if parsed.scheme.casefold() not in self._allowed_schemes:
            return False
        if not parsed.netloc or "@" in parsed.netloc:
            return False

        try:
            if parsed.username is not None or parsed.password is not None:
                return False
            hostname = parsed.hostname
        except ValueError:
            return False

        if not hostname:
            return False

        host = hostname.casefold()
        if host not in self._allowed_hosts:
            return False
        if host.rstrip(".") == "localhost":
            return False

        authority = parsed.netloc
        explicit_port = False

        if authority.startswith("["):
            closing = authority.find("]")
            if closing < 0:
                return False
            suffix = authority[closing + 1:]
            if suffix:
                if not suffix.startswith(":") or suffix == ":":
                    return False
                explicit_port = True
        else:
            if authority.count(":") > 1:
                return False
            if ":" in authority:
                if authority.rsplit(":", 1)[1] == "":
                    return False
                explicit_port = True

        if explicit_port:
            try:
                port = parsed.port
            except ValueError:
                return False
            if port is None or port not in self._allowed_ports:
                return False

        ip_address = None
        if "%" in host:
            return False

        try:
            ip_address = ipaddress.ip_address(host)
        except ValueError:
            pass

        if ip_address is not None:
            if (
                ip_address.is_loopback
                or ip_address.is_private
                or ip_address.is_link_local
                or ip_address.is_unspecified
            ):
                return False

            for network in self._blocked_networks:
                candidate = ip_address
                if (
                    candidate.version == 6
                    and candidate.ipv4_mapped is not None
                    and network.version == 4
                ):
                    candidate = candidate.ipv4_mapped
                if candidate.version == network.version and candidate in network:
                    return False

        return True