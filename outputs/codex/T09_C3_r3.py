import hashlib
import re
from urllib.parse import quote


_HEADER_NAME_RE = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")
_METHOD_RE = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")


def _encode_query_component(value):
    if not isinstance(value, str):
        raise ValueError("query keys and values must be strings")
    return quote(value, safe="-._~", encoding="utf-8", errors="strict")


def canonicalize(method, path, query, headers, body, options) -> str:
    if not isinstance(method, str) or not method.strip():
        raise ValueError("method must be a non-empty string")
    if not _METHOD_RE.fullmatch(method):
        raise ValueError("malformed method")

    if not isinstance(path, str):
        raise ValueError("path must be a string")
    if "\r" in path or "\n" in path:
        raise ValueError("malformed path")

    if not isinstance(query, list):
        raise ValueError("query must be a list")

    encoded_query = []
    for pair in query:
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            raise ValueError("malformed query pair")
        key, value = pair
        encoded_query.append((_encode_query_component(key), _encode_query_component(value)))
    encoded_query.sort()
    query_part = "&".join(f"{key}={value}" for key, value in encoded_query)

    if not isinstance(headers, dict):
        raise ValueError("headers must be a dictionary")

    normalized_headers = {}
    for name, value in headers.items():
        if not isinstance(name, str) or not _HEADER_NAME_RE.fullmatch(name):
            raise ValueError("malformed header name")
        if not isinstance(value, str):
            raise ValueError("malformed header value")
        normalized_name = name.lower()
        normalized_value = re.sub(r"\s+", " ", value.strip())
        if normalized_name in normalized_headers:
            raise ValueError("duplicate header names after normalization")
        normalized_headers[normalized_name] = normalized_value

    if not isinstance(options, dict):
        raise ValueError("options must be a dictionary")

    ignored_headers = options.get("ignored_headers", [])
    if not isinstance(ignored_headers, list):
        raise ValueError("ignored_headers must be a list")

    ignored = set()
    for name in ignored_headers:
        if not isinstance(name, str) or not _HEADER_NAME_RE.fullmatch(name):
            raise ValueError("malformed ignored header name")
        ignored.add(name.lower())

    header_part = "\n".join(
        f"{name}:{normalized_headers[name]}"
        for name in sorted(normalized_headers)
        if name not in ignored
    )

    if isinstance(body, str):
        body_bytes = body.encode("utf-8")
    elif isinstance(body, bytes):
        body_bytes = body
    else:
        raise ValueError("body must be str or bytes")

    body_digest = hashlib.sha256(body_bytes).hexdigest()

    return "\n".join((
        method.upper(),
        path,
        query_part,
        header_part,
        body_digest,
    ))
