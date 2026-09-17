import hashlib
import re
from urllib.parse import quote

_TOKEN_RE = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")
_WHITESPACE_RE = re.compile(r"\s+")


def canonicalize(method, path, query, headers, body, options) -> str:
    if not isinstance(method, str) or not method or not method.strip():
        raise ValueError("method must be a non-empty string")
    if any(ord(char) < 0x20 or ord(char) == 0x7F for char in method):
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
            raise ValueError("query entries must be two-element pairs")
        key, value = pair
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValueError("query keys and values must be strings")
        encoded_key = quote(key, safe="-._~")
        encoded_value = quote(value, safe="-._~")
        encoded_query.append((encoded_key, encoded_value))

    encoded_query.sort(key=lambda item: (item[0], item[1]))
    canonical_query = "&".join(
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

    canonical_headers = {}
    for name, value in headers.items():
        if not isinstance(name, str) or not _TOKEN_RE.fullmatch(name):
            raise ValueError("malformed header name")
        if not isinstance(value, str) or "\r" in value or "\n" in value:
            raise ValueError("malformed header value")

        normalized_name = name.lower()
        if normalized_name in ignored:
            continue

        normalized_value = _WHITESPACE_RE.sub(" ", value.strip())
        if normalized_name in canonical_headers:
            raise ValueError("duplicate header names after normalization")
        canonical_headers[normalized_name] = normalized_value

    canonical_header_block = "\n".join(
        f"{name}:{canonical_headers[name]}"
        for name in sorted(canonical_headers)
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
        canonical_query,
        canonical_header_block,
        body_digest,
    ))