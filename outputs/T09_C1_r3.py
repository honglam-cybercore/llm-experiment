import hashlib
from urllib.parse import quote


def canonicalize(method, path, query, headers, body, options) -> str:
    # Validate method
    if not isinstance(method, str) or not method.strip():
        raise ValueError("Missing or empty method")
    
    method = method.upper()
    
    # Process query parameters
    query_pairs = []
    if query is not None:
        if not isinstance(query, list):
            raise ValueError("Malformed query data")
        
        for item in query:
            if not isinstance(item, (list, tuple)):
                raise ValueError("Malformed query data")
            try:
                if len(item) != 2:
                    raise ValueError("Malformed query data")
                key, value = item
            except (ValueError, TypeError):
                raise ValueError("Malformed query data")
            
            try:
                encoded_key = quote(str(key), safe='')
                encoded_value = quote(str(value), safe='')
                query_pairs.append((encoded_key, encoded_value))
            except Exception:
                raise ValueError("Malformed query data")
        
        query_pairs.sort()
    
    query_string = "&".join(f"{k}={v}" for k, v in query_pairs)
    
    # Process headers
    if not isinstance(headers, dict):
        raise ValueError("Malformed header data")
    
    canonical_headers = {}
    try:
        ignored_headers_list = []
        if options and isinstance(options, dict):
            ignored_headers_list = options.get("ignored_headers", []) or []
        
        ignored_headers_lower = set()
        for h in ignored_headers_list:
            ignored_headers_lower.add(str(h).lower())
        
        for header_name, header_value in headers.items():
            if not isinstance(header_name, str):
                raise ValueError("Malformed header data")
            if not isinstance(header_value, str):
                raise ValueError("Malformed header data")
            
            name_lower = header_name.lower()
            if name_lower not in ignored_headers_lower:
                normalized_value = header_value.strip()
                normalized_value = ' '.join(normalized_value.split())
                canonical_headers[name_lower] = normalized_value
    except ValueError:
        raise
    except (AttributeError, TypeError, KeyError):
        raise ValueError("Malformed header data")
    
    headers_string = "\n".join(f"{k}: {v}" for k, v in sorted(canonical_headers.items()))
    
    # Process body
    if isinstance(body, str):
        body_bytes = body.encode('utf-8')
    elif isinstance(body, bytes):
        body_bytes = body
    else:
        raise ValueError("Invalid body type")
    
    body_hash = hashlib.sha256(body_bytes).hexdigest()
    
    # Build canonical representation
    return "\n".join([method, path, query_string, headers_string, body_hash])
