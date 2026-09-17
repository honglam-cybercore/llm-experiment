import hashlib
import re
from urllib.parse import quote

_TOKEN_RE = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")
_WHITESPACE_RE = re.compile(r"\s+")


def canonicalize(method, path, query, headers, body, options) -> str:
    if not isinstance(method, str) or not method or not method.strip():
        raise ValueError("method must be a non-empty string")
    if "\r" in method or "\n" in method:
        raise ValueError("method contains invalid characters")
    method = method.upper()

    if not isinstance(path, str):
        raise ValueError("path must be a string")
    if "\r" in path or "\n" in path:
        raise ValueError("path contains invalid characters")

    if not isinstance(query, list):
        raise ValueError("query must be a list")

    encoded_query = []
    for pair in query:
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            raise ValueError("malformed query pair")
        key, value = pair
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValueError("query keys and values must be strings")
        if "\r" in key or "\n" in key or "\r" in value or "\n" in value:
            raise ValueError("query contains invalid characters")
        encoded_key = quote(key, safe="-._~")
        encoded_value = quote(value, safe="-._~")
        encoded_query.append((encoded_key, encoded_value))

    encoded_query.sort()
    query_part = "&".join(
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
        if not isinstance(name, str) or not _TOKEN_RE.fullmatch(name):
            raise ValueError("malformed ignored header name")
        ignored.add(name.lower())

    canonical_headers = []
    for name, value in headers.items():
        if (
            not isinstance(name, str)
            or not _TOKEN_RE.fullmatch(name)
            or not isinstance(value, str)
        ):
            raise ValueError("malformed header data")
        if "\r" in value or "\n" in value:
            raise ValueError("header value contains invalid characters")

        lowered_name = name.lower()
        if lowered_name in ignored:
            continue

        normalized_value = _WHITESPACE_RE.sub(" ", value.strip())
        canonical_headers.append((lowered_name, normalized_value))

    canonical_headers.sort()
    headers_part = "\n".join(
        f"{name}:{value}" for name, value in canonical_headers
    )

    if isinstance(body, str):
        body_bytes = body.encode("utf-8")
    elif isinstance(body, bytes):
        body_bytes = body
    else:
        raise ValueError("body must be str or bytes")

    body_digest = hashlib.sha256(body_bytes).hexdigest()

    return "\n".join((
        method,
        path,
        query_part,
        headers_part,
        body_digest,
    ))