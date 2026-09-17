import hashlib
from urllib.parse import quote

def canonicalize(method, path, query, headers, body, options) -> str:
    # Validate and normalize method
    if not isinstance(method, str) or not method.strip():
        raise ValueError("Method is missing or empty")
    method_upper = method.upper().strip()
    
    # Normalize path
    path_str = str(path) if path is not None else ""
    
    # Process query parameters
    query_parts = []
    if query:
        if not isinstance(query, list):
            raise ValueError("Query must be a list")
        
        for param in query:
            if not isinstance(param, (list, tuple)) or len(param) != 2:
                raise ValueError("Query parameters must be [key, value] pairs")
            
            try:
                key, value = param
                key_str = str(key) if key is not None else ""
                value_str = str(value) if value is not None else ""
                encoded_key = quote(key_str, safe='')
                encoded_value = quote(value_str, safe='')
                query_parts.append((encoded_key, encoded_value))
            except (TypeError, AttributeError) as e:
                raise ValueError(f"Malformed query data: {e}")
    
    # Sort query parts by encoded key, then by encoded value
    query_parts.sort()
    query_string = "&".join(f"{k}={v}" for k, v in query_parts)
    
    # Process headers
    header_lines = []
    if headers:
        if not isinstance(headers, dict):
            raise ValueError("Headers must be a dict")
        
        ignored_headers = (options or {}).get("ignored_headers", [])
        ignored_set = {name.lower() for name in (ignored_headers or [])}
        
        try:
            for name, value in headers.items():
                if not isinstance(name, str):
                    raise ValueError("Header names must be strings")
                
                name_lower = name.lower()
                if name_lower in ignored_set:
                    continue
                
                value_str = "" if value is None else str(value)
                value_normalized = " ".join(value_str.split())
                header_lines.append((name_lower, value_normalized))
        except (TypeError, AttributeError) as e:
            raise ValueError(f"Malformed header data: {e}")
        
        # Sort headers by name
        header_lines.sort()
    
    # Hash the body
    if isinstance(body, str):
        body_bytes = body.encode('utf-8')
    elif isinstance(body, bytes):
        body_bytes = body
    elif body is None:
        body_bytes = b""
    else:
        body_bytes = str(body).encode('utf-8')
    
    body_hash = hashlib.sha256(body_bytes).hexdigest()
    
    # Build canonical representation
    headers_str = "\n".join(f"{name}: {value}" for name, value in header_lines)
    
    return "\n".join([
        method_upper,
        path_str,
        query_string,
        headers_str,
        body_hash
    ])
