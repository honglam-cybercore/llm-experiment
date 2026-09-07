from urllib.parse import urlparse
import ipaddress

class URLValidator:
    def __init__(self, allowed_schemes, allowed_hosts, allowed_ports, blocked_networks):
        self.allowed_schemes = set(allowed_schemes) if allowed_schemes else set()
        self.allowed_hosts = set(allowed_hosts) if allowed_hosts else set()
        self.allowed_ports = set(allowed_ports) if allowed_ports else set()
        
        self.blocked_networks = []
        if blocked_networks:
            for network in blocked_networks:
                try:
                    self.blocked_networks.append(ipaddress.ip_network(network, strict=False))
                except (ValueError, TypeError):
                    pass
    
    def validate(self, url):
        if not isinstance(url, str):
            return False
        
        if not url:
            return False
        
        try:
            parsed = urlparse(url)
        except:
            return False
        
        scheme = parsed.scheme
        hostname = parsed.hostname
        port = parsed.port
        
        if not scheme or not hostname:
            return False
        
        if scheme not in self.allowed_schemes:
            return False
        
        try:
            ip = ipaddress.ip_address(hostname)
            for network in self.blocked_networks:
                if ip in network:
                    return False
        except ValueError:
            pass
        
        if hostname not in self.allowed_hosts:
            return False
        
        if port is not None:
            if port not in self.allowed_ports:
                return False
        
        return True
