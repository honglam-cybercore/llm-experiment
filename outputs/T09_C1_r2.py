import hashlib
from urllib.parse import quote

def canonicalize(method, path, query, headers, body, options):
    if not method or not isinstance(method, str) or not method.strip():
        raise ValueError("Missing or empty method")
    
    method = method.upper()
    
    path = str(path) if path is not None else ""
    
    if not isinstance(query, list):
        raise ValueError("Malformed query data")
    
    encoded_query = []
    for item in query:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise ValueError("Malformed query data")
        key, value = item
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValueError("Malformed query data")
        encoded_key = quote(key, safe='')
        encoded_value = quote(value, safe='')
        encoded_query.append((encoded_key, encoded_value))
    
    encoded_query.sort()
    
    if not isinstance(headers, dict):
        raise ValueError("Malformed header data")
    
    ignored_headers = set()
    if options and isinstance(options, dict) and "ignored_headers" in options:
        ignored = options["ignored_headers"]
        if isinstance(ignored, list):
            ignored_headers = {h.lower() if isinstance(h, str) else str(h).lower() for h in ignored}
    
    canonical_headers = {}
    for name, value in headers.items():
        if not isinstance(name, str) or not isinstance(value, str):
            raise ValueError("Malformed header data")
        
        lower_name = name.lower()
        if lower_name in ignored_headers:
            continue
        
        trimmed_value = value.strip()
        canonical_value = ' '.join(trimmed_value.split())
        canonical_headers[lower_name] = canonical_value
    
    sorted_headers = sorted(canonical_headers.items())
    
    if isinstance(body, str):
        body_bytes = body.encode('utf-8')
    elif isinstance(body, bytes):
        body_bytes = body
    else:
        body_bytes = str(body).encode('utf-8')
    
    body_hash = hashlib.sha256(body_bytes).hexdigest()
    
    parts = [method, path]
    
    for key, value in encoded_query:
        parts.append(f"{key}={value}")
    
    for name, value in sorted_headers:
        parts.append(f"{name}: {value}")
    
    parts.append(body_hash)
    
    return '\n'.join(parts)
