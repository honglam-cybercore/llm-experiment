from ipaddress import ip_address, ip_network
from urllib.parse import urlsplit


class URLValidator:
    def __init__(self, allowed_schemes, allowed_hosts, allowed_ports, blocked_networks) -> None:
        self.allowed_schemes = {
            value.lower()
            for value in allowed_schemes
            if isinstance(value, str)
        }
        self.allowed_hosts = {
            value.strip("[]").lower()
            for value in allowed_hosts
            if isinstance(value, str)
        }
        self.allowed_ports = {
            value
            for value in allowed_ports
            if isinstance(value, int) and not isinstance(value, bool)
        }

        networks = []
        for value in blocked_networks:
            if isinstance(value, str):
                try:
                    networks.append(ip_network(value, strict=False))
                except ValueError:
                    continue
        self.blocked_networks = tuple(networks)

    def validate(self, url) -> bool:
        if not isinstance(url, str) or not url or url != url.strip():
            return False

        if any(character.isspace() or ord(character) < 32 or ord(character) == 127
               for character in url):
            return False

        try:
            parsed = urlsplit(url)

            if not parsed.scheme or not parsed.netloc:
                return False

            if parsed.scheme.lower() not in self.allowed_schemes:
                return False

            if "@" in parsed.netloc:
                return False

            hostname = parsed.hostname
            if not hostname:
                return False

            hostname = hostname.lower()
            if hostname == "localhost":
                return False

            if hostname not in self.allowed_hosts:
                return False

            netloc = parsed.netloc
            if netloc.startswith("["):
                closing_bracket = netloc.find("]")
                if closing_bracket < 0:
                    return False
                suffix = netloc[closing_bracket + 1:]
                if suffix and not suffix.startswith(":"):
                    return False
                explicit_port = suffix.startswith(":")
            else:
                if netloc.count(":") > 1:
                    return False
                explicit_port = ":" in netloc

            port = parsed.port
            if explicit_port and (port is None or port not in self.allowed_ports):
                return False

            try:
                address = ip_address(hostname)
            except ValueError:
                address = None

            if address is not None:
                if (
                    address.is_loopback
                    or address.is_private
                    or address.is_link_local
                    or address.is_reserved
                    or address.is_unspecified
                    or address.is_multicast
                ):
                    return False

                if any(address in network for network in self.blocked_networks):
                    return False

                mapped = getattr(address, "ipv4_mapped", None)
                if mapped is not None and any(
                    mapped in network for network in self.blocked_networks
                ):
                    return False

            return True
        except Exception:
            return False