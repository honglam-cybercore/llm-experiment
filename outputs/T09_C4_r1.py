import hashlib
from urllib.parse import quote

def canonicalize(method, path, query, headers, body, options):
    if not isinstance(method, str):
        raise ValueError("Missing or invalid method")
    
    method_upper = method.strip().upper()
    if not method_upper:
        raise ValueError("Empty method")
    
    if not isinstance(query, list):
        raise ValueError("Query must be a list")
    
    encoded_query = []
    for item in query:
        if not isinstance(item, list) or len(item) != 2:
            raise ValueError("Each query parameter must be a [key, value] pair")
        key, value = item
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValueError("Query parameter key and value must be strings")
        
        encoded_key = quote(key, safe='')
        encoded_value = quote(value, safe='')
        encoded_query.append((encoded_key, encoded_value))
    
    encoded_query.sort()
    query_string = '&'.join(f"{k}={v}" for k, v in encoded_query)
    
    if not isinstance(headers, dict):
        raise ValueError("Headers must be a dict")
    
    ignored_headers = set()
    if options and isinstance(options, dict):
        ignored_list = options.get('ignored_headers', [])
        if isinstance(ignored_list, list):
            ignored_headers = set(h.lower() for h in ignored_list if isinstance(h, str))
    
    processed_headers = {}
    for name, value in headers.items():
        if not isinstance(name, str) or not isinstance(value, str):
            raise ValueError("Header names and values must be strings")
        
        name_lower = name.lower()
        
        if name_lower in ignored_headers:
            continue
        
        normalized_value = ' '.join(value.split())
        processed_headers[name_lower] = normalized_value
    
    sorted_headers = sorted(processed_headers.items())
    headers_string = '\n'.join(f"{name}: {value}" for name, value in sorted_headers)
    
    if isinstance(body, str):
        body_bytes = body.encode('utf-8')
    elif isinstance(body, bytes):
        body_bytes = body
    else:
        raise ValueError("Body must be str or bytes")
    
    body_hash = hashlib.sha256(body_bytes).hexdigest()
    
    canonical_parts = [method_upper, path, query_string, headers_string, body_hash]
    canonical = '\n'.join(canonical_parts)
    
    return canonical
