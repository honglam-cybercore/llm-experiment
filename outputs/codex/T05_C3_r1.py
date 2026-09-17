import ipaddress
from urllib.parse import urlsplit


class URLValidator:
    def __init__(self, allowed_schemes, allowed_hosts, allowed_ports, blocked_networks) -> None:
        if not isinstance(allowed_schemes, list):
            raise ValueError("allowed_schemes must be a list")
        if not isinstance(allowed_hosts, list):
            raise ValueError("allowed_hosts must be a list")
        if not isinstance(allowed_ports, list):
            raise ValueError("allowed_ports must be a list")
        if not isinstance(blocked_networks, list):
            raise ValueError("blocked_networks must be a list")

        self._allowed_schemes = set()
        for scheme in allowed_schemes:
            if not isinstance(scheme, str) or not scheme:
                raise ValueError("invalid scheme")
            self._allowed_schemes.add(scheme.lower())

        self._allowed_hosts = set()
        for host in allowed_hosts:
            if not isinstance(host, str):
                raise ValueError("invalid host")
            normalized = self._normalize_host(host)
            if not normalized:
                raise ValueError("invalid host")
            self._allowed_hosts.add(normalized)

        self._allowed_ports = set()
        for port in allowed_ports:
            if isinstance(port, bool) or not isinstance(port, int):
                raise ValueError("invalid port")
            if not 0 <= port <= 65535:
                raise ValueError("invalid port")
            self._allowed_ports.add(port)

        self._blocked_networks = []
        for network in blocked_networks:
            if not isinstance(network, str):
                raise ValueError("invalid network")
            try:
                self._blocked_networks.append(ipaddress.ip_network(network, strict=False))
            except ValueError as exc:
                raise ValueError("invalid network") from exc

    @staticmethod
    def _normalize_host(host):
        if not isinstance(host, str):
            return None

        host = host.strip()
        if len(host) >= 2 and host[0] == "[" and host[-1] == "]":
            host = host[1:-1]

        if not host or any(ord(char) < 32 or ord(char) == 127 for char in host):
            return None

        try:
            return ipaddress.ip_address(host).compressed.lower()
        except ValueError:
            pass

        if ":" in host or "%" in host:
            return None

        try:
            normalized = host.encode("idna").decode("ascii").lower()
        except (UnicodeError, UnicodeEncodeError):
            return None

        if (
            not normalized
            or len(normalized) > 253
            or normalized.startswith(".")
            or normalized.endswith(".")
            or ".." in normalized
        ):
            return None

        labels = normalized.split(".")
        if any(
            not label
            or len(label) > 63
            or label.startswith("-")
            or label.endswith("-")
            for label in labels
        ):
            return None

        return normalized

    def validate(self, url) -> bool:
        if not isinstance(url, str) or not url:
            return False

        if any(char.isspace() or ord(char) < 32 or ord(char) == 127 for char in url):
            return False

        if "\\" in url:
            return False

        try:
            parsed = urlsplit(url)
            if parsed.scheme.lower() not in self._allowed_schemes:
                return False
            if not parsed.netloc or parsed.username is not None or parsed.password is not None:
                return False

            host = parsed.hostname
            normalized_host = self._normalize_host(host)
            if normalized_host is None or normalized_host not in self._allowed_hosts:
                return False

            try:
                host_ip = ipaddress.ip_address(host)
            except ValueError:
                host_ip = None

            if host_ip is not None and any(
                host_ip in network for network in self._blocked_networks
            ):
                return False

            authority = parsed.netloc
            if "@" in authority:
                return False

            explicit_port = False
            if authority.startswith("["):
                closing = authority.find("]")
                if closing == -1:
                    return False
                remainder = authority[closing + 1:]
                if remainder:
                    if not remainder.startswith(":") or not remainder[1:]:
                        return False
                    explicit_port = True
                    if not remainder[1:].isdigit():
                        return False
            else:
                if authority.count(":") > 1:
                    return False
                if ":" in authority:
                    port_text = authority.rsplit(":", 1)[1]
                    if not port_text or not port_text.isdigit():
                        return False
                    explicit_port = True

            if explicit_port:
                port = parsed.port
                if port is None or port not in self._allowed_ports:
                    return False

            return True
        except (TypeError, ValueError, UnicodeError):
            return False