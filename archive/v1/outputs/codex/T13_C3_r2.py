import ipaddress
from urllib.parse import urlsplit


class URLValidator:
    def __init__(self, allowed_schemes, allowed_hosts, allowed_ports, blocked_networks) -> None:
        self._valid_configuration = True

        try:
            self._allowed_schemes = {
                scheme.strip().lower()
                for scheme in allowed_schemes
                if isinstance(scheme, str) and scheme.strip()
            }
            if any(
                not isinstance(scheme, str) or not scheme.strip()
                for scheme in allowed_schemes
            ):
                self._valid_configuration = False
        except (TypeError, AttributeError):
            self._allowed_schemes = set()
            self._valid_configuration = False

        try:
            normalized_hosts = []
            for host in allowed_hosts:
                if not isinstance(host, str):
                    self._valid_configuration = False
                    continue
                normalized = self._normalize_host(host)
                if normalized is None:
                    self._valid_configuration = False
                else:
                    normalized_hosts.append(normalized)
            self._allowed_hosts = set(normalized_hosts)
        except TypeError:
            self._allowed_hosts = set()
            self._valid_configuration = False

        try:
            self._allowed_ports = set()
            for port in allowed_ports:
                if isinstance(port, bool) or not isinstance(port, int):
                    self._valid_configuration = False
                elif 0 <= port <= 65535:
                    self._allowed_ports.add(port)
                else:
                    self._valid_configuration = False
        except TypeError:
            self._allowed_ports = set()
            self._valid_configuration = False

        try:
            self._blocked_networks = []
            for network in blocked_networks:
                if not isinstance(network, str):
                    self._valid_configuration = False
                    continue
                try:
                    self._blocked_networks.append(
                        ipaddress.ip_network(network, strict=False)
                    )
                except ValueError:
                    self._valid_configuration = False
        except TypeError:
            self._blocked_networks = []
            self._valid_configuration = False

    @staticmethod
    def _normalize_host(host):
        if not isinstance(host, str) or not host:
            return None

        host = host.strip().rstrip(".")
        if not host or any(ch.isspace() or ord(ch) < 32 or ord(ch) == 127 for ch in host):
            return None

        try:
            address = ipaddress.ip_address(host)
            return address.compressed.lower()
        except ValueError:
            pass

        if ":" in host or "/" in host or "\\" in host:
            return None

        labels = host.split(".")
        encoded_labels = []

        for label in labels:
            if not label:
                return None
            try:
                encoded = label.encode("idna").decode("ascii").lower()
            except (UnicodeError, UnicodeEncodeError):
                return None
            if (
                len(encoded) > 63
                or encoded.startswith("-")
                or encoded.endswith("-")
            ):
                return None
            encoded_labels.append(encoded)

        normalized = ".".join(encoded_labels)
        return normalized if len(normalized) <= 253 else None

    @staticmethod
    def _has_explicit_port(netloc):
        if netloc.startswith("["):
            closing = netloc.find("]")
            if closing < 0:
                return False, False
            remainder = netloc[closing + 1:]
            if not remainder:
                return True, None
            if not remainder.startswith(":") or not remainder[1:]:
                return False, False
            return remainder[1:].isdigit(), True

        if netloc.count(":") > 1:
            return False, False
        if ":" not in netloc:
            return True, None

        port_text = netloc.rsplit(":", 1)[1]
        return bool(port_text) and port_text.isdigit(), True

    def validate(self, url) -> bool:
        if not self._valid_configuration or not isinstance(url, str) or not url:
            return False

        if any(ch.isspace() or ord(ch) < 32 or ord(ch) == 127 for ch in url):
            return False
        if "\\" in url or "@" in url:
            return False

        try:
            parsed = urlsplit(url)
            scheme = parsed.scheme.lower()
            if scheme not in self._allowed_schemes or not parsed.netloc:
                return False

            port_syntax_valid, has_port = self._has_explicit_port(parsed.netloc)
            if not port_syntax_valid:
                return False

            hostname = parsed.hostname
            normalized_host = self._normalize_host(hostname)
            if normalized_host is None or normalized_host not in self._allowed_hosts:
                return False

            if has_port:
                try:
                    port = parsed.port
                except ValueError:
                    return False
                if port is None or port not in self._allowed_ports:
                    return False

            try:
                host_ip = ipaddress.ip_address(hostname)
            except ValueError:
                host_ip = None

            if host_ip is not None:
                addresses = [host_ip]
                if isinstance(host_ip, ipaddress.IPv6Address) and host_ip.ipv4_mapped:
                    addresses.append(host_ip.ipv4_mapped)

                if any(
                    any(address.version == network.version and address in network
                        for network in self._blocked_networks)
                    for address in addresses
                ):
                    return False

            return True
        except (TypeError, ValueError, UnicodeError):
            return False♀♀♀♀♀♀