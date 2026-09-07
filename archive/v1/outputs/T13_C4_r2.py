import ipaddress
from urllib.parse import urlparse

class URLValidator:
    def __init__(self, allowed_schemes, allowed_hosts, allowed_ports, blocked_networks) -> None:
        self.allowed_schemes = [s.lower() for s in allowed_schemes]
        self.allowed_hosts = [h.lower() for h in allowed_hosts]
        self.allowed_ports = set(allowed_ports)
        self.blocked_networks = []
        
        for cidr in blocked_networks:
            try:
                self.blocked_networks.append(ipaddress.ip_network(cidr, strict=False))
            except ValueError:
                pass
    
    def validate(self, url) -> bool:
        if not isinstance(url, str) or not url:
            return False
        
        try:
            parsed = urlparse(url)
        except Exception:
            return False
        
        if not parsed.scheme or parsed.scheme.lower() not in self.allowed_schemes:
            return False
        
        if parsed.username is not None or parsed.password is not None:
            return False
        
        hostname = parsed.hostname
        port = parsed.port
        
        if not hostname:
            return False
        
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_loopback or ip.is_private or ip.is_link_local:
                return False
            for network in self.blocked_networks:
                if ip in network:
                    return False
        except ValueError:
            pass
        
        if hostname.lower() not in self.allowed_hosts:
            return False
        
        if port is not None and port not in self.allowed_ports:
            return False
        
        return True
