from urllib.parse import urlparse
import ipaddress

class URLValidator:
    def __init__(self, allowed_schemes, allowed_hosts, allowed_ports, blocked_networks) -> None:
        self.allowed_schemes = set(allowed_schemes) if allowed_schemes else set()
        self.allowed_hosts = set(allowed_hosts) if allowed_hosts else set()
        self.allowed_ports = set(allowed_ports) if allowed_ports else set()
        
        self.blocked_networks = []
        if blocked_networks:
            for cidr in blocked_networks:
                try:
                    self.blocked_networks.append(ipaddress.ip_network(cidr))
                except (ValueError, TypeError):
                    pass
    
    def validate(self, url) -> bool:
        if not isinstance(url, str):
            return False
        
        if not url:
            return False
        
        try:
            parsed = urlparse(url)
        except:
            return False
        
        if not parsed.scheme or parsed.scheme not in self.allowed_schemes:
            return False
        
        netloc = parsed.netloc
        if not netloc:
            return False
        
        if '@' in netloc:
            netloc = netloc.rsplit('@', 1)[1]
        
        host = None
        port = None
        
        if netloc.startswith('['):
            if ']:' in netloc:
                host, port_str = netloc.rsplit(':', 1)
                host = host.strip('[]')
                try:
                    port = int(port_str)
                except ValueError:
                    return False
            else:
                host = netloc.strip('[]')
        else:
            if ':' in netloc:
                host, port_str = netloc.rsplit(':', 1)
                try:
                    port = int(port_str)
                except ValueError:
                    return False
            else:
                host = netloc
        
        if not host:
            return False
        
        try:
            ip = ipaddress.ip_address(host)
            for network in self.blocked_networks:
                if ip in network:
                    return False
        except ValueError:
            pass
        
        if host not in self.allowed_hosts:
            return False
        
        if port is not None:
            if port not in self.allowed_ports:
                return False
        
        return True
