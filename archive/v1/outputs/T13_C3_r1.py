import ipaddress
from urllib.parse import urlparse


class URLValidator:
    def __init__(self, allowed_schemes, allowed_hosts, allowed_ports, blocked_networks) -> None:
        self.allowed_schemes = set(s.lower() if isinstance(s, str) else s for s in (allowed_schemes or []))
        self.allowed_hosts = set(h.lower() if isinstance(h, str) else h for h in (allowed_hosts or []))
        self.allowed_ports = set(allowed_ports or [])
        
        self.blocked_networks = []
        if blocked_networks:
            for network in blocked_networks:
                try:
                    self.blocked_networks.append(ipaddress.ip_network(network, strict=False))
                except (ValueError, TypeError):
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
        
        scheme = parsed.scheme.lower() if parsed.scheme else ""
        if not scheme or scheme not in self.allowed_schemes:
            return False
        
        host = parsed.hostname
        if not host:
            return False
        
        host_lower = host.lower()
        
        try:
            host_ip = ipaddress.ip_address(host)
            for network in self.blocked_networks:
                if host_ip in network:
                    return False
        except (ValueError, TypeError):
            pass
        
        if host_lower not in self.allowed_hosts:
            return False
        
        try:
            port = parsed.port
        except ValueError:
            return False
        
        if port is not None and port not in self.allowed_ports:
            return False
        
        return True
