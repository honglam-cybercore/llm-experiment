import hashlib
import urllib.parse


def canonicalize(method, path, query, headers, body, options) -> str:
    # Validate method
    if not method:
        raise ValueError("Missing or empty method")
    
    if not isinstance(method, str):
        raise ValueError("Method must be a string")
    
    method = method.upper()
    
    # Process body - compute SHA-256 hash
    if isinstance(body, str):
        body_bytes = body.encode('utf-8')
    elif isinstance(body, bytes):
        body_bytes = body
    else:
        raise ValueError("Body must be str or bytes")
    
    body_hash = hashlib.sha256(body_bytes).hexdigest()
    
    # Process query parameters
    processed_query = []
    if query:
        if not isinstance(query, (list, tuple)):
            raise ValueError("Query must be a list or tuple")
        
        for item in query:
            if not isinstance(item, (list, tuple)) or len(item) != 2:
                raise ValueError("Each query parameter must be a 2-element sequence")
            
            key, value = item
            
            # Convert to string and percent encode
            try:
                key_str = str(key)
                value_str = str(value)
                encoded_key = urllib.parse.quote(key_str, safe='')
                encoded_value = urllib.parse.quote(value_str, safe='')
                processed_query.append((encoded_key, encoded_value))
            except Exception as e:
                raise ValueError(f"Malformed query data: {e}")
    
    # Sort by encoded key, then by encoded value
    processed_query.sort(key=lambda x: (x[0], x[1]))
    
    # Reconstruct query string
    query_string = '&'.join(f"{k}={v}" for k, v in processed_query)
    
    # Process headers
    headers = headers or {}
    if not isinstance(headers, dict):
        raise ValueError("Headers must be a dict")
    
    ignored_headers = set()
    if options and isinstance(options, dict) and "ignored_headers" in options:
        try:
            ignored_headers = {str(h).lower() for h in options["ignored_headers"]}
        except Exception as e:
            raise ValueError(f"Malformed ignored_headers: {e}")
    
    processed_headers = {}
    
    for name, value in headers.items():
        # Both should be strings
        if not isinstance(name, str):
            raise ValueError("Header names must be strings")
        if not isinstance(value, str):
            raise ValueError("Header values must be strings")
        
        name_lower = name.lower()
        
        # Skip ignored headers
        if name_lower in ignored_headers:
            continue
        
        # Normalize value: strip leading/trailing whitespace, collapse internal whitespace
        normalized_value = ' '.join(value.split())
        
        processed_headers[name_lower] = normalized_value
    
    # Sort headers by name
    sorted_headers = sorted(processed_headers.items())
    
    # Build canonical representation
    parts = [method, path or '']
    
    if query_string:
        parts.append(query_string)
    
    for header_name, header_value in sorted_headers:
        parts.append(f"{header_name}: {header_value}")
    
    parts.append(body_hash)
    
    return '\n'.join(parts)
