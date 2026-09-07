from urllib.parse import urlparse
import ipaddress


class URLValidator:
    def __init__(self, allowed_schemes, allowed_hosts, allowed_ports, blocked_networks) -> None:
        self.allowed_schemes = [s.lower() for s in allowed_schemes]
        self.allowed_hosts = set()
        for h in allowed_hosts:
            try:
                ip = ipaddress.ip_address(h)
                self.allowed_hosts.add(str(ip))
            except ValueError:
                self.allowed_hosts.add(h.lower())
        
        self.allowed_ports = set(allowed_ports)
        
        self.blocked_networks = []
        for network in blocked_networks:
            try:
                self.blocked_networks.append(ipaddress.ip_network(network, strict=False))
            except Exception:
                pass

    def validate(self, url) -> bool:
        if not isinstance(url, str) or not url:
            return False
        
        try:
            parsed = urlparse(url)
        except Exception:
            return False
        
        if not parsed.scheme or parsed.scheme.lower() not in self.allowed_schemes:
            return False
        
        if parsed.username is not None or parsed.password is not None:
            return False
        
        hostname = parsed.hostname
        if not hostname:
            return False
        
        try:
            ip = ipaddress.ip_address(hostname)
            
            if ip.is_loopback or ip.is_private or ip.is_link_local:
                return False
            
            for network in self.blocked_networks:
                if ip in network:
                    return False
            
            if str(ip) not in self.allowed_hosts:
                return False
            
        except ValueError:
            if hostname.lower() not in self.allowed_hosts:
                return False
        
        if parsed.port is not None and parsed.port not in self.allowed_ports:
            return False
        
        return True
