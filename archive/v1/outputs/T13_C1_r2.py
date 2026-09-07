from urllib.parse import urlparse
from ipaddress import ip_address, ip_network

class URLValidator:
    def __init__(self, allowed_schemes, allowed_hosts, allowed_ports, blocked_networks) -> None:
        self.allowed_schemes = set(allowed_schemes) if allowed_schemes else set()
        self.allowed_hosts = set(h.lower() for h in (allowed_hosts or []))
        self.allowed_ports = set(allowed_ports) if allowed_ports else set()
        self.blocked_networks = []
        
        if blocked_networks:
            for network in blocked_networks:
                try:
                    self.blocked_networks.append(ip_network(network, strict=False))
                except ValueError:
                    pass
    
    def validate(self, url) -> bool:
        if not isinstance(url, str):
            return False
        
        if not url:
            return False
        
        try:
            parsed = urlparse(url)
        except Exception:
            return False
        
        if parsed.scheme not in self.allowed_schemes:
            return False
        
        host = parsed.hostname
        if not host:
            return False
        
        host = host.lower()
        
        try:
            host_ip = ip_address(host)
            for network in self.blocked_networks:
                if host_ip in network:
                    return False
        except ValueError:
            pass
        
        if host not in self.allowed_hosts:
            return False
        
        if parsed.port is not None:
            if parsed.port not in self.allowed_ports:
                return False
        
        return True
