import ipaddress
from urllib.parse import urlsplit


def _normalize_allowed_host(host):
    if not isinstance(host, str):
        return None
    value = host.lower()
    if len(value) >= 2 and value[0] == "[" and value[-1] == "]":
        value = value[1:-1]
    return value


def _parse_blocked_networks(networks):
    result = []
    try:
        iterator = iter(networks)
    except TypeError:
        return result

    for network in iterator:
        if not isinstance(network, str):
            continue
        try:
            result.append(ipaddress.ip_network(network, strict=False))
        except ValueError:
            continue
    return result


class URLValidator:
    def __init__(self, allowed_schemes, allowed_hosts, allowed_ports, blocked_networks) -> None:
        self._allowed_schemes = {
            value.lower()
            for value in allowed_schemes
            if isinstance(value, str)
        }

        self._allowed_hosts = {
            value
            for value in (
                _normalize_allowed_host(host) for host in allowed_hosts
            )
            if value is not None
        }

        self._allowed_ports = {
            port
            for port in allowed_ports
            if isinstance(port, int)
            and not isinstance(port, bool)
            and 0 <= port <= 65535
        }

        self._blocked_networks = _parse_blocked_networks(blocked_networks)

    def validate(self, url) -> bool:
        if not isinstance(url, str) or not url:
            return False

        try:
            parsed = urlsplit(url)
        except (TypeError, ValueError):
            return False

        if (
            not parsed.scheme
            or parsed.scheme.lower() not in self._allowed_schemes
            or not parsed.netloc
            or parsed.username is not None
            or parsed.password is not None
        ):
            return False

        if any(ord(character) < 32 or ord(character) == 127 for character in url):
            return False

        if "\\" in parsed.netloc or "@" in parsed.netloc:
            return False

        try:
            hostname = parsed.hostname
        except ValueError:
            return False

        if not hostname:
            return False

        hostname = hostname.lower()
        if hostname not in self._allowed_hosts:
            return False

        if hostname.rstrip(".") == "localhost":
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
                or address.is_multicast
                or any(
                    address.version == network.version
                    and address in network
                    for network in self._blocked_networks
                )
            ):
                return False

        netloc = parsed.netloc
        if netloc.startswith("["):
            closing = netloc.find("]")
            if closing < 0:
                return False
            suffix = netloc[closing + 1:]
            if not suffix:
                explicit_port = False
                port = None
            elif suffix.startswith(":") and suffix[1:].isdigit():
                explicit_port = True
                try:
                    port = parsed.port
                except ValueError:
                    return False
            else:
                return False
        else:
            colon_count = netloc.count(":")
            if colon_count == 0:
                explicit_port = False
                port = None
            elif colon_count == 1:
                port_text = netloc.rsplit(":", 1)[1]
                if not port_text.isdigit():
                    return False
                explicit_port = True
                try:
                    port = parsed.port
                except ValueError:
                    return False
            else:
                return False

        if explicit_port and (port is None or port not in self._allowed_ports):
            return False

        return True
