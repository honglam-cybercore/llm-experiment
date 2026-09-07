from urllib.parse import urlparse
import ipaddress


class URLValidator:
    def __init__(self, allowed_schemes, allowed_hosts, allowed_ports, blocked_networks) -> None:
        self.allowed_schemes_lower = {s.lower() for s in (allowed_schemes or [])}
        self.allowed_hosts_lower = {h.lower() for h in (allowed_hosts or [])}
        self.allowed_ports = allowed_ports or []
        self.blocked_networks = blocked_networks or []
        
        self.parsed_blocked_networks = []
        for network in self.blocked_networks:
            try:
                self.parsed_blocked_networks.append(ipaddress.ip_network(network, strict=False))
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
        
        if parsed.scheme.lower() not in self.allowed_schemes_lower:
            return False
        
        hostname = parsed.hostname
        if not hostname:
            return False
        
        try:
            ip = ipaddress.ip_address(hostname)
            for network in self.parsed_blocked_networks:
                if ip in network:
                    return False
        except ValueError:
            pass
        
        if hostname.lower() not in self.allowed_hosts_lower:
            return False
        
        if parsed.port is not None:
            if parsed.port not in self.allowed_ports:
                return False
        
        return True
