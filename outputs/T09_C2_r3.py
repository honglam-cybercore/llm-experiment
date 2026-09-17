import hashlib
from urllib.parse import quote


def canonicalize(method, path, query, headers, body, options) -> str:
    # Validate method
    if not isinstance(method, str) or not method.strip():
        raise ValueError("Missing or empty method")
    
    method = method.strip().upper()
    
    # Get ignored headers
    try:
        ignored_headers = set(h.lower() for h in (options.get('ignored_headers') or []))
    except (AttributeError, TypeError):
        ignored_headers = set()
    
    # Process headers
    if not isinstance(headers, dict):
        raise ValueError("Malformed header data")
    
    canonical_headers = []
    for name, value in headers.items():
        if not isinstance(name, str) or not isinstance(value, str):
            raise ValueError("Malformed header data")
        
        name_lower = name.lower()
        if name_lower in ignored_headers:
            continue
        
        # Normalize whitespace in value (strip and collapse internal whitespace)
        normalized_value = ' '.join(value.split())
        canonical_headers.append((name_lower, normalized_value))
    
    canonical_headers.sort()
    
    # Process query parameters
    if not isinstance(query, list):
        raise ValueError("Malformed query data")
    
    canonical_query = []
    for pair in query:
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            raise ValueError("Malformed query data")
        key, value = pair
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValueError("Malformed query data")
        
        # Percent encode
        encoded_key = quote(key, safe='')
        encoded_value = quote(value, safe='')
        canonical_query.append((encoded_key, encoded_value))
    
    canonical_query.sort()
    
    # Process body
    if isinstance(body, str):
        body_bytes = body.encode('utf-8')
    elif isinstance(body, bytes):
        body_bytes = body
    else:
        body_bytes = b''
    
    body_hash = hashlib.sha256(body_bytes).hexdigest()
    
    # Build canonical string
    lines = [method, path]
    
    for key, value in canonical_query:
        lines.append(f"{key}={value}")
    
    for name, value in canonical_headers:
        lines.append(f"{name}: {value}")
    
    lines.append(body_hash)
    
    return '\n'.join(lines)
