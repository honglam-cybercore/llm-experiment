import hashlib
from urllib.parse import quote


def canonicalize(method, path, query, headers, body, options) -> str:
    if not method or not isinstance(method, str):
        raise ValueError("Missing or empty method")
    method = method.upper().strip()
    if not method:
        raise ValueError("Missing or empty method")
    
    if not isinstance(headers, dict):
        raise ValueError("Headers must be a dictionary")
    
    ignored_headers = options.get("ignored_headers", []) if options else []
    ignored_headers_lower = {h.lower() for h in ignored_headers}
    
    normalized_headers = {}
    for name, value in headers.items():
        if not isinstance(name, str):
            raise ValueError("Header name must be a string")
        if not isinstance(value, str):
            raise ValueError("Header value must be a string")
        
        name_lower = name.lower()
        if name_lower not in ignored_headers_lower:
            normalized_value = ' '.join(value.split())
            normalized_headers[name_lower] = normalized_value
    
    sorted_headers = sorted(normalized_headers.items())
    
    if not isinstance(query, list):
        raise ValueError("Query must be a list")
    
    normalized_query = []
    for item in query:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise ValueError("Each query item must be a [key, value] pair")
        key, value = item
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValueError("Query key and value must be strings")
        encoded_key = quote(key, safe='')
        encoded_value = quote(value, safe='')
        normalized_query.append((encoded_key, encoded_value))
    
    sorted_query = sorted(normalized_query)
    
    if isinstance(body, str):
        body_bytes = body.encode('utf-8')
    elif isinstance(body, bytes):
        body_bytes = body
    else:
        raise ValueError("Body must be str or bytes")
    
    body_hash = hashlib.sha256(body_bytes).hexdigest()
    
    canonical_parts = [method, path]
    
    for key, value in sorted_query:
        canonical_parts.append(f"{key}={value}")
    
    for name, value in sorted_headers:
        canonical_parts.append(f"{name}:{value}")
    
    canonical_parts.append(body_hash)
    
    return '\n'.join(canonical_parts)
