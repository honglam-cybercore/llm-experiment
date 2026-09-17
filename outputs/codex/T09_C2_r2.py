import hashlib
import re
from urllib.parse import quote


_WHITESPACE_RE = re.compile(r"\s+")


def canonicalize(method, path, query, headers, body, options) -> str:
    if not isinstance(method, str) or not method.strip():
        raise ValueError("method must be a non-empty string")
    if not isinstance(path, str):
        raise ValueError("path must be a string")
    if not isinstance(query, list):
        raise ValueError("query must be a list")
    if not isinstance(headers, dict):
        raise ValueError("headers must be a dictionary")
    if not isinstance(options, dict):
        raise ValueError("options must be a dictionary")
    if not isinstance(body, (str, bytes)):
        raise ValueError("body must be str or bytes")

    ignored = options.get("ignored_headers", [])
    if not isinstance(ignored, list):
        raise ValueError("ignored_headers must be a list")
    if any(not isinstance(name, str) for name in ignored):
        raise ValueError("ignored header names must be strings")
    ignored = {name.lower() for name in ignored}

    encoded_query = []
    for item in query:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise ValueError("query items must be two-element pairs")
        key, value = item
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValueError("query keys and values must be strings")
        encoded_key = quote(key, safe="-._~")
        encoded_value = quote(value, safe="-._~")
        encoded_query.append((encoded_key, encoded_value))

    encoded_query.sort()
    query_part = "&".join(f"{key}={value}" for key, value in encoded_query)

    canonical_headers = []
    for name, value in headers.items():
        if not isinstance(name, str) or not isinstance(value, str):
            raise ValueError("header names and values must be strings")
        normalized_name = name.lower()
        if not normalized_name or normalized_name in ignored:
            continue
        normalized_value = _WHITESPACE_RE.sub(" ", value.strip())
        canonical_headers.append((normalized_name, normalized_value))

    canonical_headers.sort()
    headers_part = "\n".join(
        f"{name}:{value}" for name, value in canonical_headers
    )

    body_bytes = body.encode("utf-8") if isinstance(body, str) else body
    body_digest = hashlib.sha256(body_bytes).hexdigest()

    return "\n".join(
        (
            method.strip().upper(),
            path,
            query_part,
            headers_part,
            body_digest,
        )
    )