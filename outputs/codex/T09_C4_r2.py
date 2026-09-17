import hashlib
import re
from urllib.parse import quote

_TOKEN_RE = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")
_WHITESPACE_RE = re.compile(r"\s+")


def _validate_text(value, field):
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise ValueError(f"{field} contains invalid control characters")
    return value


def _encode_query_component(value):
    if not isinstance(value, str):
        raise ValueError("query keys and values must be strings")
    return quote(value, safe="-._~", encoding="utf-8", errors="strict")


def canonicalize(method, path, query, headers, body, options) -> str:
    if not isinstance(method, str) or not method.strip():
        raise ValueError("method must be a non-empty string")
    method = method.strip().upper()
    if not _TOKEN_RE.fullmatch(method):
        raise ValueError("method contains invalid characters")

    path = _validate_text(path, "path")

    if not isinstance(query, list):
        raise ValueError("query must be a list")

    encoded_query = []
    for pair in query:
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            raise ValueError("each query item must be a two-element pair")
        key = _encode_query_component(pair[0])
        value = _encode_query_component(pair[1])
        encoded_query.append((key, value))
    encoded_query.sort(key=lambda item: (item[0], item[1]))
    canonical_query = "&".join(
        f"{key}={value}" for key, value in encoded_query
    )

    if not isinstance(headers, dict):
        raise ValueError("headers must be a dictionary")
    if not isinstance(options, dict):
        raise ValueError("options must be a dictionary")

    ignored = options.get("ignored_headers", [])
    if not isinstance(ignored, list):
        raise ValueError("ignored_headers must be a list")

    ignored_names = set()
    for name in ignored:
        if not isinstance(name, str) or not _TOKEN_RE.fullmatch(name):
            raise ValueError("ignored header names must be valid strings")
        ignored_names.add(name.lower())

    normalized_headers = {}
    for name, value in headers.items():
        if not isinstance(name, str) or not _TOKEN_RE.fullmatch(name):
            raise ValueError("header names must be valid strings")
        if not isinstance(value, str):
            raise ValueError("header values must be strings")
        if any(char in value for char in "\r\n"):
            raise ValueError("header values must not contain CR or LF")
        normalized_name = name.lower()
        if normalized_name in normalized_headers:
            raise ValueError("duplicate header names after normalization")
        if normalized_name not in ignored_names:
            normalized_headers[normalized_name] = _WHITESPACE_RE.sub(
                " ", value.strip()
            )

    canonical_headers = "\n".join(
        f"{name}:{normalized_headers[name]}"
        for name in sorted(normalized_headers)
    )

    if isinstance(body, str):
        body_bytes = body.encode("utf-8")
    elif isinstance(body, bytes):
        body_bytes = body
    else:
        raise ValueError("body must be a string or bytes")

    body_hash = hashlib.sha256(body_bytes).hexdigest()

    return "\n".join(
        (method, path, canonical_query, canonical_headers, body_hash)
    )