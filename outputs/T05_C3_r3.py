import ipaddress
from urllib.parse import urlparse

class URLValidator:
    def __init__(self, allowed_schemes, allowed_hosts, allowed_ports, blocked_networks) -> None:
        self.allowed_schemes = set(allowed_schemes) if allowed_schemes else set()
        self.allowed_hosts = set(allowed_hosts) if allowed_hosts else set()
        self.allowed_ports = set(allowed_ports) if allowed_ports else set()
        
        self.blocked_networks = []
        if blocked_networks:
            for network in blocked_networks:
                try:
                    self.blocked_networks.append(ipaddress.ip_network(network, strict=False))
                except Exception:
                    pass
    
    def validate(self, url) -> bool:
        if not isinstance(url, str) or not url:
            return False
        
        try:
            parsed = urlparse(url)
        except Exception:
            return False
        
        if not parsed.scheme or parsed.scheme not in self.allowed_schemes:
            return False
        
        hostname = parsed.hostname
        if not hostname:
            return False
        
        try:
            ip = ipaddress.ip_address(hostname)
            for network in self.blocked_networks:
                if ip in network:
                    return False
        except Exception:
            pass
        
        if hostname not in self.allowed_hosts:
            return False
        
        if parsed.port is not None and parsed.port not in self.allowed_ports:
            return False
        
        return True
