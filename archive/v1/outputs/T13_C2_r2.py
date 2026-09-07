from urllib.parse import urlparse
import ipaddress

class URLValidator:
    def __init__(self, allowed_schemes, allowed_hosts, allowed_ports, blocked_networks) -> None:
        self.allowed_schemes = set(s.lower() for s in allowed_schemes)
        self.allowed_hosts = set(h.lower() for h in allowed_hosts)
        self.allowed_ports = set(allowed_ports)
        self.blocked_networks = []
        
        for network_str in blocked_networks:
            try:
                self.blocked_networks.append(ipaddress.ip_network(network_str, strict=False))
            except (ValueError, TypeError):
                pass
    
    def validate(self, url) -> bool:
        if not isinstance(url, str) or not url:
            return False
        
        try:
            parsed = urlparse(url)
        except Exception:
            return False
        
        if parsed.username is not None or parsed.password is not None:
            return False
        
        scheme = parsed.scheme.lower() if parsed.scheme else ""
        if not scheme or scheme not in self.allowed_schemes:
            return False
        
        try:
            hostname = parsed.hostname
        except Exception:
            return False
        
        if not hostname:
            return False
        
        if hostname.lower() not in self.allowed_hosts:
            return False
        
        try:
            ip = ipaddress.ip_address(hostname)
            
            for network in self.blocked_networks:
                if ip in network:
                    return False
            
            if ip.is_loopback or ip.is_private or ip.is_link_local:
                return False
        except ValueError:
            pass
        
        try:
            port = parsed.port
        except Exception:
            return False
        
        if port is not None and port not in self.allowed_ports:
            return False
        
        return True
