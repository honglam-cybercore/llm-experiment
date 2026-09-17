import hashlib
import re
from urllib.parse import quote

_TOKEN_RE = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")
_WHITESPACE_RE = re.compile(r"\s+")


def canonicalize(method, path, query, headers, body, options) -> str:
    if not isinstance(method, str) or not method.strip():
        raise ValueError("method must be a non-empty string")
    if not _TOKEN_RE.fullmatch(method):
        raise ValueError("malformed method")

    if not isinstance(path, str) or "\r" in path or "\n" in path:
        raise ValueError("malformed path")

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
            raise ValueError("malformed query data")
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

    ignored = options.get("ignored_headers", [])
    if not isinstance(ignored, list):
        raise ValueError("ignored_headers must be a list")

    ignored_names = set()
    for name in ignored:
        if not isinstance(name, str) or not _TOKEN_RE.fullmatch(name):
            raise ValueError("malformed ignored header name")
        ignored_names.add(name.lower())

    normalized_headers = {}
    for name, value in headers.items():
        if (
            not isinstance(name, str)
            or not _TOKEN_RE.fullmatch(name)
            or not isinstance(value, str)
            or "\r" in value
            or "\n" in value
        ):
            raise ValueError("malformed header data")

        normalized_name = name.lower()
        if normalized_name in ignored_names:
            continue

        normalized_value = _WHITESPACE_RE.sub(" ", value.strip())
        if normalized_name in normalized_headers:
            raise ValueError("duplicate header names")
        normalized_headers[normalized_name] = normalized_value

    header_part = "\n".join(
        f"{name}:{normalized_headers[name]}"
        for name in sorted(normalized_headers)
    )

    if isinstance(body, str):
        body_bytes = body.encode("utf-8")
    elif isinstance(body, bytes):
        body_bytes = body
    else:
        raise ValueError("body must be str or bytes")

    body_digest = hashlib.sha256(body_bytes).hexdigest()

    return "\n".join([
        method.upper(),
        path,
        query_part,
        header_part,
        body_digest,
    ])