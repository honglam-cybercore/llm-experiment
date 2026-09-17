from urllib.parse import urlsplit
import ipaddress


def _normalize_host(host):
    if not isinstance(host, str):
        return None

    host = host.strip().lower()
    if len(host) >= 2 and host.startswith("[") and host.endswith("]"):
        host = host[1:-1]

    if not host:
        return None

    if "%" in host:
        return None

    try:
        return host.encode("idna").decode("ascii").rstrip(".")
    except UnicodeError:
        return None


class URLValidator:
    def __init__(self, allowed_schemes, allowed_hosts, allowed_ports, blocked_networks) -> None:
        self._allowed_schemes = {
            scheme.lower()
            for scheme in allowed_schemes
            if isinstance(scheme, str)
        }
        self._allowed_hosts = {
            normalized
            for host in allowed_hosts
            if (normalized := _normalize_host(host)) is not None
        }
        self._allowed_ports = {
            port for port in allowed_ports
            if isinstance(port, int) and not isinstance(port, bool)
        }

        self._blocked_networks = []
        for network in blocked_networks:
            if not isinstance(network, str):
                continue
            try:
                self._blocked_networks.append(ipaddress.ip_network(network, strict=False))
            except ValueError:
                continue

    def validate(self, url) -> bool:
        if not isinstance(url, str) or not url or url != url.strip():
            return False

        if any(character.isspace() or ord(character) < 32 or ord(character) == 127
               for character in url):
            return False

        try:
            parsed = urlsplit(url)
            scheme = parsed.scheme.lower()
            hostname = parsed.hostname
        except (TypeError, ValueError):
            return False

        if scheme not in self._allowed_schemes or not parsed.netloc or not hostname:
            return False

        normalized_host = _normalize_host(hostname)
        if normalized_host is None or normalized_host not in self._allowed_hosts:
            return False

        try:
            port = parsed.port
        except ValueError:
            return False

        authority = parsed.netloc.rsplit("@", 1)[-1]
        explicit_port = False

        if authority.startswith("["):
            closing = authority.find("]")
            if closing < 0:
                return False
            suffix = authority[closing + 1:]
            if suffix:
                if not suffix.startswith(":") or not suffix[1:].isdigit():
                    return False
                explicit_port = True
        else:
            colon_count = authority.count(":")
            if colon_count > 1:
                return False
            if colon_count == 1:
                host_part, port_part = authority.rsplit(":", 1)
                if not host_part or not port_part.isdigit():
                    return False
                explicit_port = True

        if explicit_port and port not in self._allowed_ports:
            return False

        try:
            host_ip = ipaddress.ip_address(hostname)
        except ValueError:
            host_ip = None

        if host_ip is not None:
            for network in self._blocked_networks:
                if host_ip.version == network.version and host_ip in network:
                    return False

        return True