from urllib.parse import urlparse
import ipaddress

class URLValidator:
    def __init__(self, allowed_schemes, allowed_hosts, allowed_ports, blocked_networks) -> None:
        self.allowed_schemes = [s.lower() for s in allowed_schemes]
        self.allowed_hosts = [h.lower() for h in allowed_hosts]
        self.allowed_ports = set(allowed_ports)
        
        self.blocked_networks = []
        for network in blocked_networks:
            try:
                self.blocked_networks.append(ipaddress.ip_network(network, strict=False))
            except:
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
        
        if not parsed.scheme or parsed.scheme.lower() not in self.allowed_schemes:
            return False
        
        hostname = parsed.hostname
        if not hostname:
            return False
        
        try:
            ip_obj = ipaddress.ip_address(hostname)
            
            if ip_obj.is_loopback or ip_obj.is_private or ip_obj.is_link_local:
                return False
            
            for blocked_net in self.blocked_networks:
                if ip_obj in blocked_net:
                    return False
        except ValueError:
            pass
        
        if hostname.lower() not in self.allowed_hosts:
            return False
        
        if parsed.port is not None and parsed.port not in self.allowed_ports:
            return False
        
        return True
