import ipaddress
import re
from urllib.parse import urlsplit


class URLValidator:
    def __init__(self, allowed_schemes, allowed_hosts, allowed_ports, blocked_networks) -> None:
        self._allowed_schemes = {
            str(scheme).lower() for scheme in allowed_schemes
            if isinstance(scheme, str)
        }
        self._allowed_hosts = {
            self._normalize_host(host) for host in allowed_hosts
            if isinstance(host, str) and self._normalize_host(host) is not None
        }
        self._allowed_ports = {
            port for port in allowed_ports
            if isinstance(port, int) and not isinstance(port, bool)
        }
        self._blocked_networks = []

        for network in blocked_networks:
            try:
                self._blocked_networks.append(
                    ipaddress.ip_network(network, strict=False)
                )
            except (TypeError, ValueError):
                continue

    @staticmethod
    def _normalize_host(host):
        host = host.strip().lower()

        if host.startswith("[") and host.endswith("]"):
            host = host[1:-1]

        try:
            return ipaddress.ip_address(host).compressed.lower()
        except ValueError:
            pass

        if host.endswith("."):
            host = host[:-1]

        if not host or len(host) > 253:
            return None

        try:
            ascii_host = host.encode("idna").decode("ascii").lower()
        except (UnicodeError, ValueError):
            return None

        labels = ascii_host.split(".")
        if any(
            not label
            or len(label) > 63
            or label.startswith("-")
            or label.endswith("-")
            or not re.fullmatch(r"[a-z0-9-]+", label)
            for label in labels
        ):
            return None

        return ascii_host

    def validate(self, url) -> bool:
        if not isinstance(url, str) or not url:
            return False

        if any(ord(char) <= 32 or ord(char) == 127 for char in url):
            return False

        if "\\" in url or "@" in url:
            return False

        try:
            parsed = urlsplit(url)
        except ValueError:
            return False

        if parsed.scheme.lower() not in self._allowed_schemes:
            return False

        if not parsed.netloc or parsed.hostname is None:
            return False

        raw_netloc = parsed.netloc
        if raw_netloc.startswith("["):
            closing = raw_netloc.find("]")
            if closing < 0:
                return False
            suffix = raw_netloc[closing + 1:]
            if suffix and not suffix.startswith(":"):
                return False
            explicit_port = bool(suffix)
        else:
            if raw_netloc.count(":") > 1:
                return False
            explicit_port = ":" in raw_netloc

        try:
            host = self._normalize_host(parsed.hostname)
        except (TypeError, ValueError):
            return False

        if host is None or host not in self._allowed_hosts:
            return False

        try:
            port = parsed.port
        except ValueError:
            return False

        if explicit_port:
            if port is None or port not in self._allowed_ports:
                return False

        try:
            address = ipaddress.ip_address(parsed.hostname)
        except ValueError:
            address = None

        if address is not None:
            for network in self._blocked_networks:
                if address.version == network.version and address in network:
                    return False
                if (
                    address.version == 6
                    and address.ipv4_mapped is not None
                    and network.version == 4
                    and address.ipv4_mapped in network
                ):
                    return False

        return True