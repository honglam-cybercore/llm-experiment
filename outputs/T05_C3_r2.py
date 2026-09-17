from urllib.parse import urlparse
from ipaddress import ip_address, ip_network, AddressValueError


class URLValidator:
    def __init__(self, allowed_schemes, allowed_hosts, allowed_ports, blocked_networks) -> None:
        self.allowed_schemes = set(s.lower() for s in (allowed_schemes or []) if s)
        self.allowed_hosts = set(h.lower() for h in (allowed_hosts or []) if h)
        self.allowed_ports = set(allowed_ports or [])
        
        self.blocked_networks = []
        if blocked_networks:
            for cidr in blocked_networks:
                try:
                    self.blocked_networks.append(ip_network(cidr, strict=False))
                except (AddressValueError, ValueError, TypeError):
                    pass
    
    def validate(self, url) -> bool:
        if not isinstance(url, str) or not url:
            return False
        
        try:
            parsed = urlparse(url)
        except Exception:
            return False
        
        scheme = parsed.scheme.lower() if parsed.scheme else ""
        if not scheme or scheme not in self.allowed_schemes:
            return False
        
        hostname = parsed.hostname
        if not hostname:
            return False
        
        hostname = hostname.lower()
        
        if hostname not in self.allowed_hosts:
            return False
        
        try:
            ip = ip_address(hostname)
            for network in self.blocked_networks:
                if ip in network:
                    return False
        except (AddressValueError, ValueError):
            pass
        
        try:
            port = parsed.port
            if port is not None:
                if port not in self.allowed_ports:
                    return False
        except (ValueError, TypeError):
            return False
        
        return True
