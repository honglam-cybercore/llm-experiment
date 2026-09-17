import hashlib
import re
from urllib.parse import quote


_TOKEN_RE = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")


def _encode_query_component(value):
    if not isinstance(value, str):
        raise ValueError("query keys and values must be strings")
    if "\r" in value or "\n" in value:
        raise ValueError("query data contains forbidden characters")
    return quote(value, safe="-_.~")


def canonicalize(method, path, query, headers, body, options) -> str:
    if not isinstance(method, str) or not method.strip():
        raise ValueError("method must be a non-empty string")
    if "\r" in method or "\n" in method:
        raise ValueError("invalid method")
    normalized_method = method.strip().upper()

    if not isinstance(path, str):
        raise ValueError("path must be a string")
    if "\r" in path or "\n" in path:
        raise ValueError("invalid path")

    if not isinstance(query, list):
        raise ValueError("query must be a list")

    encoded_query = []
    for pair in query:
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            raise ValueError("query entries must be two-element pairs")
        key = _encode_query_component(pair[0])
        value = _encode_query_component(pair[1])
        encoded_query.append((key, value))
    encoded_query.sort(key=lambda item: (item[0], item[1]))

    if not isinstance(headers, dict):
        raise ValueError("headers must be a dictionary")

    if not isinstance(options, dict):
        raise ValueError("options must be a dictionary")
    ignored = options.get("ignored_headers", [])
    if not isinstance(ignored, list):
        raise ValueError("ignored_headers must be a list")

    ignored_names = set()
    for name in ignored:
        if not isinstance(name, str):
            raise ValueError("ignored header names must be strings")
        normalized = name.strip().lower()
        if not normalized or not _TOKEN_RE.fullmatch(normalized):
            raise ValueError("invalid ignored header name")
        ignored_names.add(normalized)

    normalized_headers = {}
    for name, value in headers.items():
        if not isinstance(name, str) or not _TOKEN_RE.fullmatch(name):
            raise ValueError("invalid header name")
        if not isinstance(value, str):
            raise ValueError("header values must be strings")
        if "\r" in value or "\n" in value:
            raise ValueError("header values contain forbidden characters")

        normalized_name = name.lower()
        if normalized_name in normalized_headers:
            raise ValueError("duplicate header names after normalization")
        if normalized_name not in ignored_names:
            normalized_headers[normalized_name] = " ".join(value.split())

    if isinstance(body, str):
        body_bytes = body.encode("utf-8")
    elif isinstance(body, bytes):
        body_bytes = body
    else:
        raise ValueError("body must be a string or bytes")

    body_digest = hashlib.sha256(body_bytes).hexdigest()

    query_text = "&".join(f"{key}={value}" for key, value in encoded_query)
    header_text = "\n".join(
        f"{name}:{normalized_headers[name]}"
        for name in sorted(normalized_headers)
    )

    return "\n".join((normalized_method, path, query_text, header_text, body_digest))