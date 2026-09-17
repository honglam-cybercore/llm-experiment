import hashlib
from urllib.parse import quote

def canonicalize(method, path, query, headers, body, options) -> str:
    if not isinstance(method, str) or not method.strip():
        raise ValueError("Missing or empty method")
    
    method = method.strip().upper()
    
    canonical_query = ""
    if query:
        if not isinstance(query, list):
            raise ValueError("Malformed query data")
        
        query_pairs = []
        for pair in query:
            if not isinstance(pair, (list, tuple)) or len(pair) != 2:
                raise ValueError("Malformed query data")
            key, value = pair
            encoded_key = quote(str(key), safe='')
            encoded_value = quote(str(value), safe='')
            query_pairs.append((encoded_key, encoded_value))
        
        query_pairs.sort()
        canonical_query = "&".join(f"{k}={v}" for k, v in query_pairs)
    
    canonical_headers = ""
    if headers:
        if not isinstance(headers, dict):
            raise ValueError("Malformed header data")
        
        ignored_headers = set()
        if options and isinstance(options, dict) and "ignored_headers" in options:
            ignored_list = options["ignored_headers"]
            if not isinstance(ignored_list, list):
                raise ValueError("Malformed header data")
            ignored_headers = set(str(h).lower() for h in ignored_list)
        
        processed_headers = []
        for name, value in headers.items():
            if not isinstance(name, str) or not isinstance(value, str):
                raise ValueError("Malformed header data")
            
            name_lower = name.lower()
            if name_lower in ignored_headers:
                continue
            
            value_clean = ' '.join(value.split())
            processed_headers.append((name_lower, value_clean))
        
        processed_headers.sort()
        canonical_headers = "\n".join(f"{k}: {v}" for k, v in processed_headers)
    
    if isinstance(body, str):
        body_bytes = body.encode('utf-8')
    elif isinstance(body, bytes):
        body_bytes = body
    else:
        raise ValueError("Body must be str or bytes")
    
    body_hash = hashlib.sha256(body_bytes).hexdigest()
    
    parts = [
        method,
        path,
        canonical_query,
        canonical_headers,
        body_hash
    ]
    
    return "\n".join(parts)
