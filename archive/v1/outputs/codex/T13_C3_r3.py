import ipaddress
import re
from urllib.parse import urlsplit


class URLValidator:
    def __init__(self, allowed_schemes, allowed_hosts, allowed_ports, blocked_networks) -> None:
        self._allowed_schemes = frozenset(
            scheme.lower() for scheme in allowed_schemes
            if isinstance(scheme, str) and scheme
        )
        self._allowed_hosts = frozenset(
            self._canonical_host(host) for host in allowed_hosts
            if isinstance(host, str) and host
        )

        if any(
            isinstance(port, bool) or not isinstance(port, int) or not 0 <= port <= 65535
            for port in allowed_ports
        ):
            raise ValueError("Invalid allowed port")

        self._allowed_ports = frozenset(allowed_ports)

        try:
            self._blocked_networks = tuple(
                ipaddress.ip_network(network, strict=True)
                for network in blocked_networks
            )
        except (TypeError, ValueError) as exc:
            raise ValueError("Invalid blocked network") from exc

    @staticmethod
    def _canonical_host(host):
        if not isinstance(host, str):
            raise ValueError("Invalid host")

        host = host.strip()
        if host.startswith("[") and host.endswith("]"):
            host = host[1:-1]

        if not host or "%" in host:
            raise ValueError("Invalid host")

        try:
            address = ipaddress.ip_address(host)
            return address.compressed.lower()
        except ValueError:
            pass

        if len(host) > 253:
            raise ValueError("Invalid host")

        try:
            canonical = host.rstrip(".").encode("idna").decode("ascii").lower()
        except UnicodeError as exc:
            raise ValueError("Invalid host") from exc

        if not canonical or any(
            not label or len(label) > 63 or label.startswith("-") or label.endswith("-")
            for label in canonical.split(".")
        ):
            raise ValueError("Invalid host")

        return canonical

    @staticmethod
    def _explicit_port(netloc):
        if netloc.startswith("["):
            closing = netloc.find("]")
            if closing < 0:
                raise ValueError("Malformed IPv6 host")
            remainder = netloc[closing + 1:]
            if not remainder:
                return None
            if not remainder.startswith(":") or not remainder[1:].isdigit():
                raise ValueError("Malformed port")
            return int(remainder[1:])

        if netloc.count(":") > 1:
            raise ValueError("Malformed host")

        if ":" not in netloc:
            return None

        port = netloc.rsplit(":", 1)[1]
        if not port.isdigit():
            raise ValueError("Malformed port")
        return int(port)

    def validate(self, url) -> bool:
        if not isinstance(url, str) or not url:
            return False

        if any(ord(char) < 0x20 or ord(char) == 0x7F or char.isspace() for char in url):
            return False

        try:
            parsed = urlsplit(url)
            if parsed.scheme.lower() not in self._allowed_schemes:
                return False
            if not parsed.netloc or "@" in parsed.netloc:
                return False

            explicit_port = self._explicit_port(parsed.netloc)
            if explicit_port is not None:
                if not 0 <= explicit_port <= 65535:
                    return False
                if explicit_port not in self._allowed_ports:
                    return False

            host = self._canonical_host(parsed.hostname)
            if host not in self._allowed_hosts:
                return False

            address = ipaddress.ip_address(host)
            addresses = [address]
            if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped:
                addresses.append(address.ipv4_mapped)

            return not any(
                blocked.version == candidate.version and candidate in blocked
                for candidate in addresses
                for blocked in self._blocked_networks
            )
        except (AttributeError, TypeError, ValueError):
            return False