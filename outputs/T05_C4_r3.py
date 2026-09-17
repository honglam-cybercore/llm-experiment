from urllib.parse import urlparse
from ipaddress import ip_address, ip_network, AddressValueError


class URLValidator:
    def __init__(self, allowed_schemes, allowed_hosts, allowed_ports, blocked_networks) -> None:
        self.allowed_schemes = [s.lower() for s in allowed_schemes] if allowed_schemes else []
        self.allowed_ports = list(allowed_ports) if allowed_ports else []
        self.blocked_networks = []
        
        self.allowed_hosts = []
        if allowed_hosts:
            for host in allowed_hosts:
                try:
                    ip = ip_address(host)
                    self.allowed_hosts.append(str(ip))
                except (AddressValueError, ValueError):
                    self.allowed_hosts.append(host.lower())
        
        if blocked_networks:
            for network in blocked_networks:
                try:
                    self.blocked_networks.append(ip_network(network, strict=False))
                except (AddressValueError, ValueError):
                    pass
    
    def validate(self, url) -> bool:
        try:
            if not isinstance(url, str) or not url.strip():
                return False
            
            parsed = urlparse(url)
            
            if parsed.scheme.lower() not in self.allowed_schemes:
                return False
            
            if parsed.username is not None or parsed.password is not None:
                return False
            
            hostname = parsed.hostname
            if not hostname:
                return False
            
            if hostname == "localhost":
                return False
            
            try:
                ip = ip_address(hostname)
                
                if ip.is_loopback or ip.is_private or ip.is_link_local:
                    return False
                
                for network in self.blocked_networks:
                    if ip in network:
                        return False
                
                if str(ip) not in self.allowed_hosts:
                    return False
            
            except (AddressValueError, ValueError):
                if hostname not in self.allowed_hosts:
                    return False
            
            if parsed.port is not None and parsed.port not in self.allowed_ports:
                return False
            
            return True
        
        except Exception:
            return False
