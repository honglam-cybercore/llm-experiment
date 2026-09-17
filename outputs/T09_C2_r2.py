import hashlib
import urllib.parse

def canonicalize(method, path, query, headers, body, options) -> str:
    # Validate and process method
    if not method:
        raise ValueError("Missing or empty method")
    
    method = str(method).strip().upper()
    if not method:
        raise ValueError("Missing or empty method")
    
    # Get ignored headers
    ignored_headers = set()
    if options and isinstance(options, dict) and "ignored_headers" in options:
        ignored_headers_list = options["ignored_headers"]
        if ignored_headers_list:
            ignored_headers = {str(h).lower() for h in ignored_headers_list}
    
    # Process headers
    processed_headers = {}
    if headers and isinstance(headers, dict):
        for name, value in headers.items():
            if not isinstance(name, str):
                raise ValueError("Malformed header data")
            name_lower = name.lower()
            if name_lower in ignored_headers:
                continue
            if not isinstance(value, str):
                raise ValueError("Malformed header data")
            # Normalize whitespace: strip and collapse internal runs
            normalized_value = " ".join(value.split())
            processed_headers[name_lower] = normalized_value
    
    # Sort headers by name
    sorted_headers = sorted(processed_headers.items())
    headers_str = "\n".join(f"{name}:{value}" for name, value in sorted_headers)
    
    # Process query parameters
    encoded_query_pairs = []
    if query:
        if not isinstance(query, (list, tuple)):
            raise ValueError("Malformed query data")
        for pair in query:
            if not isinstance(pair, (list, tuple)) or len(pair) != 2:
                raise ValueError("Malformed query data")
            key, value = pair
            # Percent encode
            encoded_key = urllib.parse.quote(str(key), safe='')
            encoded_value = urllib.parse.quote(str(value), safe='')
            encoded_query_pairs.append((encoded_key, encoded_value))
    
    # Sort by encoded key, then by encoded value
    encoded_query_pairs.sort()
    
    if encoded_query_pairs:
        query_str = "&".join(f"{k}={v}" for k, v in encoded_query_pairs)
    else:
        query_str = ""
    
    # Process body
    if isinstance(body, str):
        body_bytes = body.encode('utf-8')
    elif isinstance(body, bytes):
        body_bytes = body
    else:
        raise ValueError("Body must be str or bytes")
    
    body_hash = hashlib.sha256(body_bytes).hexdigest()
    
    # Combine into canonical representation
    parts = [method, path, query_str, headers_str, body_hash]
    canonical = "\n".join(parts)
    
    return canonical
