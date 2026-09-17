import hashlib
from urllib.parse import quote


def canonicalize(method, path, query, headers, body, options) -> str:
    if not isinstance(method, str) or not method.strip():
        raise ValueError("method must be a non-empty string")

    if not isinstance(path, str):
        raise ValueError("path must be a string")

    if not isinstance(query, list):
        raise ValueError("query must be a list")

    encoded_query = []
    for item in query:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise ValueError("malformed query parameter")
        key, value = item
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValueError("query keys and values must be strings")
        encoded_query.append((
            quote(key, safe="-._~"),
            quote(value, safe="-._~"),
        ))
    encoded_query.sort()
    query_string = "&".join(f"{key}={value}" for key, value in encoded_query)

    if not isinstance(headers, dict):
        raise ValueError("headers must be a dictionary")

    ignored = set()
    if options is not None:
        if not isinstance(options, dict):
            raise ValueError("options must be a dictionary")
        ignored_headers = options.get("ignored_headers", [])
        if not isinstance(ignored_headers, list):
            raise ValueError("ignored_headers must be a list")
        for name in ignored_headers:
            if not isinstance(name, str) or not name:
                raise ValueError("malformed ignored header name")
            ignored.add(name.lower())

    canonical_headers = []
    for name, value in headers.items():
        if (
            not isinstance(name, str)
            or not name
            or any(char.isspace() for char in name)
            or ":" in name
            or "\r" in name
            or "\n" in name
            or not isinstance(value, str)
            or "\r" in value
            or "\n" in value
        ):
            raise ValueError("malformed header data")

        normalized_name = name.lower()
        if normalized_name in ignored:
            continue

        normalized_value = " ".join(value.split())
        canonical_headers.append((normalized_name, normalized_value))

    canonical_headers.sort()
    header_string = "\n".join(
        f"{name}:{value}" for name, value in canonical_headers
    )

    if isinstance(body, str):
        body_bytes = body.encode("utf-8")
    elif isinstance(body, bytes):
        body_bytes = body
    else:
        raise ValueError("body must be a string or bytes")

    body_hash = hashlib.sha256(body_bytes).hexdigest()

    return "\n".join((
        method.upper(),
        path,
        query_string,
        header_string,
        body_hash,
    ))