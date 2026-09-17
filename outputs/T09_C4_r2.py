import hashlib
from urllib.parse import quote


def canonicalize(method, path, query, headers, body, options) -> str:
    # Validate and normalize method
    if not method or not isinstance(method, str) or not method.strip():
        raise ValueError("Method must be a non-empty string")
    canonical_method = method.upper()
    
    # Normalize input parameters to default values if None
    if headers is None:
        headers = {}
    elif not isinstance(headers, dict):
        raise ValueError("Headers must be a dictionary")
    
    if query is None:
        query = []
    elif not isinstance(query, list):
        raise ValueError("Query must be a list")
    
    if options is None:
        options = {}
    elif not isinstance(options, dict):
        raise ValueError("Options must be a dictionary")
    
    # Process headers
    ignored_headers = {h.lower() for h in options.get('ignored_headers', []) if isinstance(h, str)}
    canonical_headers = {}
    
    for key, value in headers.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValueError("Header names and values must be strings")
        
        lower_key = key.lower()
        if lower_key in ignored_headers:
            continue
        
        # Normalize whitespace: strip and collapse internal whitespace
        normalized_value = ' '.join(value.split())
        canonical_headers[lower_key] = normalized_value
    
    sorted_headers = sorted(canonical_headers.items())
    
    # Process query parameters
    encoded_params = []
    for param in query:
        if not isinstance(param, (list, tuple)) or len(param) != 2:
            raise ValueError("Query parameters must be [key, value] pairs")
        
        key, value = param
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValueError("Query parameter keys and values must be strings")
        
        encoded_key = quote(key, safe='')
        encoded_value = quote(value, safe='')
        encoded_params.append((encoded_key, encoded_value))
    
    # Sort by encoded key, then by encoded value
    encoded_params.sort()
    canonical_query = '&'.join(f"{ek}={ev}" for ek, ev in encoded_params)
    
    # Process body
    if isinstance(body, str):
        body_bytes = body.encode('utf-8')
    elif isinstance(body, bytes):
        body_bytes = body
    else:
        raise ValueError("Body must be str or bytes")
    
    body_hash = hashlib.sha256(body_bytes).hexdigest()
    
    # Build canonical representation
    parts = [canonical_method, path]
    parts.extend(f"{name}: {value}" for name, value in sorted_headers)
    parts.append(canonical_query)
    parts.append(body_hash)
    
    return '\n'.join(parts)
