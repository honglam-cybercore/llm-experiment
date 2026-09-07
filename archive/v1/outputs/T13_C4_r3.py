from urllib.parse import urlparse
from ipaddress import ip_address, ip_network, AddressValueError


class URLValidator:
    def __init__(self, allowed_schemes, allowed_hosts, allowed_ports, blocked_networks) -> None:
        self.allowed_schemes = [scheme.lower() for scheme in allowed_schemes]
        self.allowed_hosts = [host.lower() for host in allowed_hosts]
        self.allowed_ports = set(allowed_ports)
        
        self.blocked_networks = []
        for network_str in blocked_networks:
            try:
                self.blocked_networks.append(ip_network(network_str, strict=False))
            except (ValueError, AddressValueError, TypeError):
                pass
    
    def validate(self, url) -> bool:
        if not isinstance(url, str):
            return False
        
        if not url.strip():
            return False
        
        try:
            parsed = urlparse(url)
            
            if parsed.username is not None or parsed.password is not None:
                return False
            
            scheme = parsed.scheme.lower() if parsed.scheme else ""
            
            if scheme not in self.allowed_schemes:
                return False
            
            hostname = parsed.hostname
            port = parsed.port
            
            if hostname is None:
                return False
            
            hostname_lower = hostname.lower()
            
            try:
                ip = ip_address(hostname)
                
                if ip.is_loopback or ip.is_private or ip.is_link_local:
                    return False
                
                for blocked_net in self.blocked_networks:
                    if ip in blocked_net:
                        return False
                
                if hostname_lower not in self.allowed_hosts:
                    return False
                    
            except (ValueError, AddressValueError):
                if hostname_lower not in self.allowed_hosts:
                    return False
            
            if port is not None:
                if port not in self.allowed_ports:
                    return False
            
            return True
            
        except Exception:
            return False
