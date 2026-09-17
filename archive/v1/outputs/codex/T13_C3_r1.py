import ipaddress
import unicodedata
from urllib.parse import urlsplit


class URLValidator:
    def __init__(self, allowed_schemes, allowed_hosts, allowed_ports, blocked_networks) -> None:
        self._valid_configuration = True

        try:
            self._allowed_schemes = {
                scheme.lower()
                for scheme in allowed_schemes
                if isinstance(scheme, str) and scheme
            }
            if len(self._allowed_schemes) != len(list(allowed_schemes)):
                self._valid_configuration = False
        except Exception:
            self._allowed_schemes = set()
            self._valid_configuration = False

        self._allowed_hosts = set()
        try:
            for host in allowed_hosts:
                normalized = self._normalize_host(host)
                if normalized is None:
                    self._valid_configuration = False
                else:
                    self._allowed_hosts.add(normalized)
        except Exception:
            self._valid_configuration = False

        try:
            self._allowed_ports = set()
            for port in allowed_ports:
                if isinstance(port, bool) or not isinstance(port, int) or not 0 <= port <= 65535:
                    self._valid_configuration = False
                else:
                    self._allowed_ports.add(port)
        except Exception:
            self._allowed_ports = set()
            self._valid_configuration = False

        self._blocked_networks = []
        try:
            for network in blocked_networks:
                if not isinstance(network, str):
                    self._valid_configuration = False
                    continue
                self._blocked_networks.append(ipaddress.ip_network(network, strict=True))
        except Exception:
            self._valid_configuration = False

    @staticmethod
    def _normalize_host(host):
        if not isinstance(host, str) or not host:
            return None

        host = host.strip()
        if not host:
            return None

        if host.startswith("[") and host.endswith("]"):
            host = host[1:-1]

        if "%" in host:
            return None

        try:
            host = unicodedata.normalize("NFKC", host).rstrip(".").lower()
            if not host:
                return None

            try:
                return str(ipaddress.ip_address(host))
            except ValueError:
                return host.encode("idna").decode("ascii")
        except (UnicodeError, ValueError):
            return None

    def validate(self, url) -> bool:
        if not self._valid_configuration or not isinstance(url, str) or not url:
            return False

        try:
            if any(ord(char) < 32 or ord(char) == 127 or char.isspace() for char in url):
                return False

            parsed = urlsplit(url)

            if parsed.scheme.lower() not in self._allowed_schemes:
                return False

            if not parsed.netloc or "@" in parsed.netloc or "\\" in parsed.netloc:
                return False

            if parsed.netloc.endswith(":"):
                return False

            host = self._normalize_host(parsed.hostname)
            if host is None or host not in self._allowed_hosts:
                return False

            port = parsed.port
            if port is not None and port not in self._allowed_ports:
                return False

            try:
                address = ipaddress.ip_address(host)
            except ValueError:
                address = None

            if address is not None:
                for network in self._blocked_networks:
                    if address.version == network.version and address in network:
                        return False

            return True
        except (ValueError, TypeError, UnicodeError):
            return False