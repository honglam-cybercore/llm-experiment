from urllib.parse import urlparse
from ipaddress import ip_address, ip_network

class URLValidator:
    def __init__(self, allowed_schemes, allowed_hosts, allowed_ports, blocked_networks) -> None:
        self.allowed_schemes = set(allowed_schemes)
        self.allowed_hosts = set(allowed_hosts)
        self.allowed_ports = set(allowed_ports)
        
        self.parsed_blocked_networks = []
        for network_str in blocked_networks:
            try:
                self.parsed_blocked_networks.append(ip_network(network_str, strict=False))
            except ValueError:
                pass
    
    def validate(self, url) -> bool:
        if not isinstance(url, str):
            return False
        
        if not url:
            return False
        
        parsed = urlparse(url)
        
        if parsed.scheme not in self.allowed_schemes:
            return False
        
        host = parsed.hostname
        if host is None:
            return False
        
        if host not in self.allowed_hosts:
            return False
        
        try:
            host_ip = ip_address(host)
            for network in self.parsed_blocked_networks:
                if host_ip in network:
                    return False
        except ValueError:
            pass
        
        try:
            port = parsed.port
            if port is not None:
                if port not in self.allowed_ports:
                    return False
        except ValueError:
            return False
        
        return True
