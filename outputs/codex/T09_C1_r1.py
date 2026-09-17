import hashlib
import re
from urllib.parse import quote


def canonicalize(method, path, query, headers, body, options) -> str:
    if not isinstance(method, str) or not method:
        raise ValueError("method must be a non-empty string")

    if not isinstance(query, list):
        raise ValueError("query must be a list")

    encoded_query = []
    for pair in query:
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            raise ValueError("malformed query pair")
        key, value = pair
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValueError("query keys and values must be strings")
        encoded_key = quote(key, safe="-_.~")
        encoded_value = quote(value, safe="-_.~")
        encoded_query.append((encoded_key, encoded_value))

    encoded_query.sort()
    query_string = "&".join(
        f"{key}={value}" for key, value in encoded_query
    )

    if not isinstance(headers, dict):
        raise ValueError("headers must be a dictionary")

    if not isinstance(options, dict):
        raise ValueError("options must be a dictionary")

    ignored_headers = options.get("ignored_headers", [])
    if not isinstance(ignored_headers, list):
        raise ValueError("ignored_headers must be a list")

    ignored = set()
    for name in ignored_headers:
        if not isinstance(name, str):
            raise ValueError("ignored header names must be strings")
        ignored.add(name.lower())

    canonical_headers = []
    for name, value in headers.items():
        if (
            not isinstance(name, str)
            or not name
            or any(char in name for char in "\r\n:")
            or not isinstance(value, str)
        ):
            raise ValueError("malformed header data")

        lower_name = name.lower()
        if lower_name in ignored:
            continue

        normalized_value = re.sub(r"\s+", " ", value.strip())
        canonical_headers.append((lower_name, normalized_value))

    canonical_headers.sort()
    headers_string = "\n".join(
        f"{name}:{value}" for name, value in canonical_headers
    )

    if isinstance(body, str):
        body_bytes = body.encode("utf-8")
    elif isinstance(body, bytes):
        body_bytes = body
    else:
        raise ValueError("body must be str or bytes")

    body_digest = hashlib.sha256(body_bytes).hexdigest()

    return "\n".join(
        (
            method.upper(),
            path if isinstance(path, str) else str(path),
            query_string,
            headers_string,
            body_digest,
        )
    )