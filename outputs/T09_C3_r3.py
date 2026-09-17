import hashlib
from typing import Union, List, Dict, Any


def canonicalize(method: str, path: str, query: List[List[str]], headers: Dict[str, str], body: Union[str, bytes], options: Dict[str, Any]) -> str:
    # Validate and normalize method
    if not method or not isinstance(method, str):
        raise ValueError("Method is missing or invalid")
    
    method = method.upper().strip()
    if not method:
        raise ValueError("Method is empty")
    
    # Process body - convert to SHA-256 hex digest
    if isinstance(body, str):
        body_bytes = body.encode('utf-8')
    elif isinstance(body, bytes):
        body_bytes = body
    else:
        raise ValueError("Body must be str or bytes")
    
    body_hash = hashlib.sha256(body_bytes).hexdigest()
    
    # Process headers
    if not isinstance(headers, dict):
        raise ValueError("Headers must be a dict")
    
    ignored_headers_set = set()
    if options and isinstance(options, dict) and "ignored_headers" in options:
        ignored_headers_list = options.get("ignored_headers", [])
        ignored_headers_set = set(h.lower() for h in ignored_headers_list)
    
    # Normalize headers: lowercase names, strip and collapse whitespace in values
    normalized_headers = {}
    for name, value in headers.items():
        if not isinstance(name, str) or not isinstance(value, str):
            raise ValueError("Header names and values must be strings")
        
        lower_name = name.lower()
        if lower_name not in ignored_headers_set:
            # Remove leading/trailing whitespace, collapse internal runs
            normalized_value = ' '.join(value.split())
            normalized_headers[lower_name] = normalized_value
    
    # Sort headers by name
    sorted_headers = sorted(normalized_headers.items())
    
    # Process query parameters
    if not isinstance(query, list):
        raise ValueError("Query must be a list")
    
    for item in query:
        if not isinstance(item, list) or len(item) != 2:
            raise ValueError("Query items must be [key, value] pairs")
        key, value = item
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValueError("Query keys and values must be strings")
    
    # Sort by encoded key, then by encoded value
    sorted_query = sorted(query, key=lambda x: (x[0], x[1]))
    
    # Build canonical representation
    canonical_parts = [method, path]
    
    # Add query parameters
    canonical_parts.extend(f"{k}={v}" for k, v in sorted_query)
    
    # Add headers
    canonical_parts.extend(f"{name}: {value}" for name, value in sorted_headers)
    
    # Add body hash
    canonical_parts.append(body_hash)
    
    return '\n'.join(canonical_parts)
