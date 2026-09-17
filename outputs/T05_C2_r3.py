from urllib.parse import urlparse
import ipaddress


class URLValidator:
    def __init__(self, allowed_schemes, allowed_hosts, allowed_ports, blocked_networks):
        self.allowed_schemes = set(s.lower() for s in (allowed_schemes or []))
        
        # Normalize allowed hosts
        self.allowed_hosts = set()
        for h in (allowed_hosts or []):
            try:
                ip = ipaddress.ip_address(h)
                self.allowed_hosts.add(str(ip))
            except ValueError:
                self.allowed_hosts.add(h.lower())
        
        self.allowed_ports = set(allowed_ports or [])
        self.blocked_networks = []
        
        for network in (blocked_networks or []):
            try:
                self.blocked_networks.append(ipaddress.ip_network(network, strict=False))
            except (ValueError, TypeError):
                pass
    
    def validate(self, url) -> bool:
        if not isinstance(url, str) or not url:
            return False
        
        try:
            parsed = urlparse(url)
        except Exception:
            return False
        
        # Reject URLs with user information
        if parsed.username is not None or parsed.password is not None:
            return False
        
        scheme = parsed.scheme.lower()
        host = parsed.hostname
        port = parsed.port
        
        # Validate scheme
        if scheme not in self.allowed_schemes:
            return False
        
        # Host must not be empty
        if not host:
            return False
        
        # Check if host is an IP address and validate it
        try:
            ip = ipaddress.ip_address(host)
            
            # Reject special IP addresses
            if ip.is_loopback or ip.is_private or ip.is_link_local:
                return False
            
            # Check against blocked networks
            for network in self.blocked_networks:
                if ip in network:
                    return False
            
            # Normalize and check if in allowed hosts
            normalized_host = str(ip)
        except ValueError:
            # Not an IP address, it's a hostname
            normalized_host = host.lower()
        
        # Check if host is in allowed_hosts
        if normalized_host not in self.allowed_hosts:
            return False
        
        # Validate port if provided
        if port is not None and port not in self.allowed_ports:
            return False
        
        return True
