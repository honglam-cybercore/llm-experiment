import ipaddress
from urllib.parse import urlparse

class URLValidator:
    def __init__(self, allowed_schemes, allowed_hosts, allowed_ports, blocked_networks) -> None:
        self.allowed_schemes = set(s.lower() for s in (allowed_schemes or []))
        self.allowed_hosts = set(h.lower() for h in (allowed_hosts or []))
        self.allowed_ports = set(allowed_ports or [])
        self.blocked_networks = []
        
        if blocked_networks:
            for network in blocked_networks:
                try:
                    self.blocked_networks.append(ipaddress.ip_network(network, strict=False))
                except (ValueError, TypeError):
                    pass
    
    def validate(self, url) -> bool:
        if not isinstance(url, str) or not url:
            return False
        
        try:
            parsed = urlparse(url)
        except:
            return False
        
        if parsed.username is not None or parsed.password is not None:
            return False
        
        scheme = (parsed.scheme or "").lower()
        if not scheme or scheme not in self.allowed_schemes:
            return False
        
        hostname = parsed.hostname
        if not hostname:
            return False
        
        hostname_lower = hostname.lower()
        
        if hostname_lower == "localhost":
            return False
        
        try:
            ip = ipaddress.ip_address(hostname)
            
            if ip.is_loopback or ip.is_private or ip.is_link_local:
                return False
            
            for network in self.blocked_networks:
                if ip in network:
                    return False
        except ValueError:
            if hostname_lower not in self.allowed_hosts:
                return False
        
        if parsed.port is not None:
            if parsed.port not in self.allowed_ports:
                return False
        
        return True
