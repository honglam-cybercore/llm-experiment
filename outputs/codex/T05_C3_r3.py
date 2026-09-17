import ipaddress
import re
from urllib.parse import urlsplit


_CONTROL_OR_SPACE = re.compile(r"[\x00-\x20\x7f]")


def _normalize_host(host):
    if not isinstance(host, str) or not host:
        raise ValueError

    try:
        ip = ipaddress.ip_address(host)
        return ip.compressed.lower()
    except ValueError:
        pass

    if host.endswith("."):
        host = host[:-1]
    if not host:
        raise ValueError

    labels = host.split(".")
    normalized = []
    for label in labels:
        if not label:
            raise ValueError
        encoded = label.encode("idna").decode("ascii").lower()
        if len(encoded) > 63:
            raise ValueError
        normalized.append(encoded)

    result = ".".join(normalized)
    if len(result) > 253:
        raise ValueError
    return result


class URLValidator:
    def __init__(self, allowed_schemes, allowed_hosts, allowed_ports, blocked_networks) -> None:
        self._valid_configuration = True

        try:
            if not isinstance(allowed_schemes, list):
                raise ValueError
            self._allowed_schemes = {
                scheme.strip().lower()
                for scheme in allowed_schemes
                if isinstance(scheme, str) and scheme.strip()
            }
            if len(self._allowed_schemes) != len(allowed_schemes):
                raise ValueError

            if not isinstance(allowed_hosts, list):
                raise ValueError
            self._allowed_hosts = {
                _normalize_host(host)
                for host in allowed_hosts
            }
            if len(self._allowed_hosts) != len(allowed_hosts):
                raise ValueError

            if not isinstance(allowed_ports, list):
                raise ValueError
            if any(
                isinstance(port, bool)
                or not isinstance(port, int)
                or not 0 <= port <= 65535
                for port in allowed_ports
            ):
                raise ValueError
            self._allowed_ports = set(allowed_ports)

            if not isinstance(blocked_networks, list):
                raise ValueError
            self._blocked_networks = tuple(
                ipaddress.ip_network(network, strict=False)
                for network in blocked_networks
                if isinstance(network, str)
            )
            if len(self._blocked_networks) != len(blocked_networks):
                raise ValueError
        except (TypeError, ValueError):
            self._valid_configuration = False
            self._allowed_schemes = set()
            self._allowed_hosts = set()
            self._allowed_ports = set()
            self._blocked_networks = ()

    def validate(self, url) -> bool:
        if not self._valid_configuration or not isinstance(url, str) or not url:
            return False

        if _CONTROL_OR_SPACE.search(url) or "\\" in url:
            return False

        try:
            parsed = urlsplit(url)
        except (TypeError, ValueError):
            return False

        if not parsed.scheme or parsed.scheme.lower() not in self._allowed_schemes:
            return False
        if not parsed.netloc:
            return False

        try:
            hostname = parsed.hostname
        except ValueError:
            return False

        if not hostname:
            return False

        try:
            normalized_host = _normalize_host(hostname)
        except (TypeError, ValueError):
            return False

        if normalized_host not in self._allowed_hosts:
            return False

        authority = parsed.netloc.rsplit("@", 1)[-1]
        explicit_port = False

        if authority.startswith("["):
            closing = authority.find("]")
            if closing < 0:
                return False
            suffix = authority[closing + 1:]
            if suffix:
                if not suffix.startswith(":") or not suffix[1:]:
                    return False
                explicit_port = True
                if not suffix[1:].isdigit():
                    return False
        else:
            colon_count = authority.count(":")
            if colon_count > 1:
                return False
            if colon_count == 1:
                host_part, port_part = authority.rsplit(":", 1)
                if not host_part or not port_part or not port_part.isdigit():
                    return False
                explicit_port = True

        try:
            port = parsed.port
        except ValueError:
            return False

        if explicit_port and (port is None or port not in self._allowed_ports):
            return False

        try:
            host_ip = ipaddress.ip_address(hostname)
        except ValueError:
            host_ip = None

        if host_ip is not None:
            if any(host_ip in network for network in self._blocked_networks):
                return False

        return True