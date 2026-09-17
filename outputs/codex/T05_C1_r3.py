import ipaddress
from urllib.parse import urlsplit


def _normalize_host(host):
    if not isinstance(host, str):
        return None

    host = host.strip()
    if len(host) >= 2 and host[0] == "[" and host[-1] == "]":
        host = host[1:-1]

    host = host.rstrip(".").lower()
    if not host:
        return None

    try:
        return ipaddress.ip_address(host).compressed.lower()
    except ValueError:
        try:
            return host.encode("idna").decode("ascii").lower()
        except (UnicodeError, ValueError):
            return host


class URLValidator:
    def __init__(self, allowed_schemes, allowed_hosts, allowed_ports, blocked_networks) -> None:
        self._allowed_schemes = {
            scheme.lower()
            for scheme in allowed_schemes
            if isinstance(scheme, str)
        }
        self._allowed_hosts = {
            normalized
            for normalized in (_normalize_host(host) for host in allowed_hosts)
            if normalized is not None
        }
        self._allowed_ports = {
            port
            for port in allowed_ports
            if isinstance(port, int) and not isinstance(port, bool)
        }

        networks = []
        for network in blocked_networks:
            if not isinstance(network, str):
                continue
            try:
                networks.append(ipaddress.ip_network(network, strict=False))
            except ValueError:
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
            scheme = parsed.scheme.lower()
            hostname = parsed.hostname
            port = parsed.port
        except (ValueError, UnicodeError):
            return False

        if not scheme or not parsed.netloc:
            return False

        if scheme not in self._allowed_schemes:
            return False

        normalized_host = _normalize_host(hostname)
        if normalized_host is None or normalized_host not in self._allowed_hosts:
            return False

        authority = parsed.netloc.rsplit("@", 1)[-1]
        explicit_port = False

        if authority.startswith("["):
            closing = authority.find("]")
            if closing < 0:
                return False
            remainder = authority[closing + 1:]
            if remainder:
                if not remainder.startswith(":") or not remainder[1:].isdigit():
                    return False
                explicit_port = True
        elif authority.count(":") == 1:
            suffix = authority.rsplit(":", 1)[1]
            if not suffix.isdigit():
                return False
            explicit_port = True
        elif authority.count(":") > 1:
            return False

        if explicit_port and port not in self._allowed_ports:
            return False

        try:
            host_ip = ipaddress.ip_address(hostname)
        except ValueError:
            host_ip = None

        if host_ip is not None:
            if any(host_ip in network for network in self._blocked_networks):
                return False

        return True