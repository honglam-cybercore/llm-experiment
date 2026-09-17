from urllib.parse import urlparse
import ipaddress

class URLValidator:
    def __init__(self, allowed_schemes, allowed_hosts, allowed_ports, blocked_networks) -> None:
        # Normalize allowed_schemes
        self.allowed_schemes = set()
        for scheme in (allowed_schemes or []):
            if isinstance(scheme, str) and scheme:
                self.allowed_schemes.add(scheme.lower())
        
        # Normalize allowed_hosts
        self.allowed_hosts = set()
        for host in (allowed_hosts or []):
            if isinstance(host, str) and host:
                try:
                    # Try to parse as IP
                    ip = ipaddress.ip_address(host)
                    self.allowed_hosts.add(str(ip))
                except ValueError:
                    # It's a hostname, lowercase it
                    self.allowed_hosts.add(host.lower())
        
        # Store allowed_ports
        self.allowed_ports = set()
        for port in (allowed_ports or []):
            if isinstance(port, int):
                self.allowed_ports.add(port)
        
        # Parse blocked networks
        self.blocked_networks = []
        for network_str in (blocked_networks or []):
            if isinstance(network_str, str) and network_str:
                try:
                    self.blocked_networks.append(ipaddress.ip_network(network_str, strict=False))
                except ValueError:
                    pass
    
    def validate(self, url) -> bool:
        try:
            if not isinstance(url, str):
                return False
            
            parsed = urlparse(url)
            
            if parsed.username is not None or parsed.password is not None:
                return False
            
            scheme = parsed.scheme.lower()
            if not scheme or scheme not in self.allowed_schemes:
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
                hostname_lower = hostname.lower()
                if hostname_lower not in self.allowed_hosts:
                    return False
            
            port = parsed.port
            if port is not None:
                if port not in self.allowed_ports:
                    return False
            
            return True
        
        except Exception:
            return False
