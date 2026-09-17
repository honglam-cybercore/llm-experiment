import hashlib
import re
from urllib.parse import quote


_HEADER_NAME_RE = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")
_WHITESPACE_RE = re.compile(r"\s+")


def _encode_query_component(value):
    if not isinstance(value, str):
        raise ValueError("query keys and values must be strings")
    return quote(value, safe="-_.~")


def canonicalize(method, path, query, headers, body, options) -> str:
    if not isinstance(method, str) or not method.strip():
        raise ValueError("method must be a non-empty string")

    if not isinstance(path, str):
        raise ValueError("path must be a string")

    if not isinstance(query, list):
        raise ValueError("query must be a list")

    encoded_query = []
    for pair in query:
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            raise ValueError("malformed query pair")
        key, value = pair
        encoded_key = _encode_query_component(key)
        encoded_value = _encode_query_component(value)
        encoded_query.append((encoded_key, encoded_value))

    encoded_query.sort()
    query_text = "&".join(
        f"{key}={value}" for key, value in encoded_query
    )

    if not isinstance(headers, dict):
        raise ValueError("headers must be a dictionary")

    normalized_headers = {}
    for name, value in headers.items():
        if (
            not isinstance(name, str)
            or not name
            or not _HEADER_NAME_RE.fullmatch(name)
            or not isinstance(value, str)
        ):
            raise ValueError("malformed header data")

        normalized_name = name.lower()
        normalized_value = _WHITESPACE_RE.sub(" ", value.strip())
        normalized_headers[normalized_name] = normalized_value

    if not isinstance(options, dict):
        raise ValueError("options must be a dictionary")

    ignored_headers = options.get("ignored_headers", [])
    if not isinstance(ignored_headers, list):
        raise ValueError("ignored_headers must be a list")

    ignored = set()
    for name in ignored_headers:
        if not isinstance(name, str):
            raise ValueError("malformed ignored header name")
        ignored.add(name.lower())

    header_lines = [
        f"{name}:{normalized_headers[name]}"
        for name in sorted(normalized_headers)
        if name not in ignored
    ]
    headers_text = "\n".join(header_lines)

    if isinstance(body, str):
        body_bytes = body.encode("utf-8")
    elif isinstance(body, bytes):
        body_bytes = body
    else:
        raise ValueError("body must be str or bytes")

    body_digest = hashlib.sha256(body_bytes).hexdigest()

    return "\n".join(
        [
            method.upper(),
            path,
            query_text,
            headers_text,
            body_digest,
        ]
    )