from urllib.parse import urlparse
from ipaddress import ip_address, ip_network, AddressValueError


class URLValidator:
    def __init__(self, allowed_schemes, allowed_hosts, allowed_ports, blocked_networks):
        self.allowed_schemes = set(s.lower() for s in (allowed_schemes or []))
        self.allowed_hosts = set(h.lower() for h in (allowed_hosts or []))
        self.allowed_ports = set(allowed_ports or [])
        self.blocked_networks = []
        
        if blocked_networks:
            for cidr in blocked_networks:
                try:
                    self.blocked_networks.append(ip_network(cidr))
                except (ValueError, AddressValueError, TypeError):
                    pass
    
    def validate(self, url):
        if not isinstance(url, str):
            return False
        
        if not url.strip():
            return False
        
        try:
            parsed = urlparse(url)
        except Exception:
            return False
        
        if not parsed.scheme or parsed.scheme not in self.allowed_schemes:
            return False
        
        host = parsed.hostname
        if not host:
            return False
        
        try:
            ip = ip_address(host)
            for blocked_net in self.blocked_networks:
                if ip in blocked_net:
                    return False
        except (ValueError, AddressValueError, TypeError):
            pass
        
        if host not in self.allowed_hosts:
            return False
        
        if parsed.port is not None:
            if parsed.port not in self.allowed_ports:
                return False
        
        return True
