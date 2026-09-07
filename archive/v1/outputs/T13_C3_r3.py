from urllib.parse import urlparse
from ipaddress import ip_address, ip_network, AddressValueError


class URLValidator:
    def __init__(self, allowed_schemes, allowed_hosts, allowed_ports, blocked_networks) -> None:
        self.allowed_schemes = set(allowed_schemes) if allowed_schemes else set()
        self.allowed_hosts = set(allowed_hosts) if allowed_hosts else set()
        self.allowed_ports = set(allowed_ports) if allowed_ports else set()
        
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
        
        try:
            scheme = parsed.scheme
            host = parsed.hostname
            port = parsed.port
        except ValueError:
            return False
        
        if not scheme or not host:
            return False
        
        if scheme not in self.allowed_schemes:
            return False
        
        try:
            host_ip = ip_address(host)
            for blocked_net in self.blocked_networks:
                if host_ip in blocked_net:
                    return False
        except (AddressValueError, ValueError):
            pass
        
        if host not in self.allowed_hosts:
            return False
        
        if port is not None:
            if port not in self.allowed_ports:
                return False
        
        return True
