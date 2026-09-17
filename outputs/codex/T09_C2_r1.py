import hashlib
import re
from urllib.parse import quote


_HEADER_NAME_RE = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")


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

    ignored = options.get("ignored_headers", [])
    if not isinstance(ignored, list):
        raise ValueError("ignored_headers must be a list")

    ignored_names = set()
    for name in ignored:
        if not isinstance(name, str) or not _HEADER_NAME_RE.fullmatch(name):
            raise ValueError("malformed ignored header name")
        ignored_names.add(name.lower())

    normalized_headers = {}
    for name, value in headers.items():
        if (
            not isinstance(name, str)
            or not _HEADER_NAME_RE.fullmatch(name)
            or not isinstance(value, str)
        ):
            raise ValueError("malformed header data")

        normalized_name = name.lower()
        if normalized_name in ignored_names:
            continue

        if normalized_name in normalized_headers:
            raise ValueError("duplicate header names")
        normalized_headers[normalized_name] = re.sub(r"\s+", " ", value.strip())

    encoded_query = []
    for pair in query:
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            raise ValueError("malformed query data")
        key, value = pair
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValueError("malformed query data")
        encoded_query.append(
            (
                quote(key, safe="-._~"),
                quote(value, safe="-._~"),
            )
        )
    encoded_query.sort()

    if isinstance(body, str):
        body_bytes = body.encode("utf-8")
    elif isinstance(body, bytes):
        body_bytes = body
    else:
        raise ValueError("body must be str or bytes")

    body_hash = hashlib.sha256(body_bytes).hexdigest()
    query_part = "&".join(f"{key}={value}" for key, value in encoded_query)
    header_part = "\n".join(
        f"{name}:{normalized_headers[name]}"
        for name in sorted(normalized_headers)
    )

    return "\n".join(
        (
            method.upper(),
            path,
            query_part,
            header_part,
            body_hash,
        )
    )