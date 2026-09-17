import hashlib
import urllib.parse

def canonicalize(method, path, query, headers, body, options) -> str:
    if not isinstance(method, str) or not method.strip():
        raise ValueError("Missing or empty method")
    method = method.strip().upper()
    
    if isinstance(body, str):
        body_bytes = body.encode('utf-8')
    elif isinstance(body, bytes):
        body_bytes = body
    else:
        raise ValueError("Body must be str or bytes")
    body_hash = hashlib.sha256(body_bytes).hexdigest()
    
    if not isinstance(headers, dict):
        raise ValueError("Headers must be a dict")
    
    ignored_headers = set()
    if options and isinstance(options, dict):
        ignored_list = options.get("ignored_headers", [])
        if isinstance(ignored_list, list):
            ignored_headers = set(h.lower() for h in ignored_list)
    
    canonical_headers = {}
    for name, value in headers.items():
        if not isinstance(name, str) or not isinstance(value, str):
            raise ValueError("Header names and values must be strings")
        
        name_lower = name.lower()
        if name_lower not in ignored_headers:
            value_normalized = ' '.join(value.split())
            canonical_headers[name_lower] = value_normalized
    
    sorted_headers = sorted(canonical_headers.items())
    
    if not isinstance(query, list):
        raise ValueError("Query must be a list")
    
    processed_query = []
    for item in query:
        if not isinstance(item, list) or len(item) != 2:
            raise ValueError("Query items must be [key, value] pairs")
        key, value = item
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValueError("Query keys and values must be strings")
        
        key_encoded = urllib.parse.quote(key, safe='')
        value_encoded = urllib.parse.quote(value, safe='')
        processed_query.append((key_encoded, value_encoded))
    
    processed_query.sort()
    
    parts = [method, path]
    
    if processed_query:
        query_str = '&'.join(f"{k}={v}" for k, v in processed_query)
        parts.append(query_str)
    else:
        parts.append('')
    
    for name, value in sorted_headers:
        parts.append(f"{name}: {value}")
    
    parts.append(body_hash)
    
    return '\n'.join(parts)
