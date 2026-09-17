import ipaddress
import re
from urllib.parse import urlsplit


_CONTROL_OR_SPACE = re.compile(r"[\x00-\x20\x7f]")


def _normalise_host(host):
    if not isinstance(host, str) or not host:
        return None

    if host.startswith("[") and host.endswith("]"):
        host = host[1:-1]

    if not host or _CONTROL_OR_SPACE.search(host):
        return None
    if any(character in host for character in "/\\@%"):
        return None

    try:
        return str(ipaddress.ip_address(host))
    except ValueError:
        try:
            return host.encode("idna").decode("ascii").lower()
        except (UnicodeError, ValueError):
            return None


def _is_valid_scheme(scheme):
    return isinstance(scheme, str) and bool(
        re.fullmatch(r"[A-Za-z][A-Za-z0-9+.-]*", scheme)
    )


class URLValidator:
    def __init__(self, allowed_schemes, allowed_hosts, allowed_ports, blocked_networks) -> None:
        self._configuration_valid = True

        if not isinstance(allowed_schemes, list):
            self._configuration_valid = False
            allowed_schemes = []
        self._allowed_schemes = set()
        for scheme in allowed_schemes:
            if not _is_valid_scheme(scheme):
                self._configuration_valid = False
                continue
            self._allowed_schemes.add(scheme.lower())

        if not isinstance(allowed_hosts, list):
            self._configuration_valid = False
            allowed_hosts = []
        self._allowed_hosts = set()
        for host in allowed_hosts:
            normalised = _normalise_host(host)
            if normalised is None:
                self._configuration_valid = False
            else:
                self._allowed_hosts.add(normalised)

        if not isinstance(allowed_ports, list):
            self._configuration_valid = False
            allowed_ports = []
        self._allowed_ports = set()
        for port in allowed_ports:
            if isinstance(port, bool) or not isinstance(port, int) or not 0 <= port <= 65535:
                self._configuration_valid = False
            else:
                self._allowed_ports.add(port)

        if not isinstance(blocked_networks, list):
            self._configuration_valid = False
            blocked_networks = []
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
        if _CONTROL_OR_SPACE.search(url):
            return False

        try:
            parsed = urlsplit(url)
        except (TypeError, ValueError):
            return False

        if parsed.scheme.lower() not in self._allowed_schemes:
            return False
        if not parsed.netloc or parsed.hostname is None:
            return False
        if parsed.username is not None or parsed.password is not None:
            return False

        host = _normalise_host(parsed.hostname)
        if host is None or host not in self._allowed_hosts:
            return False

        authority = parsed.netloc
        if "@" in authority:
            return False

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
                if authority.rsplit(":", 1)[1] == "":
                    return False
                explicit_port = True

        try:
            port = parsed.port
        except ValueError:
            return False

        if explicit_port and port not in self._allowed_ports:
            return False

        try:
            ip_host = ipaddress.ip_address(host)
        except ValueError:
            ip_host = None

        if ip_host is not None:
            for blocked_network in self._blocked_networks:
                if ip_host in blocked_network:
                    return False

        return True