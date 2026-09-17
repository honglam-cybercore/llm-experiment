def canonicalize(method, path, query, headers, body, options) -> str:
    import hashlib
    import re
    from urllib.parse import quote

    if not isinstance(method, str) or not method:
        raise ValueError("method must be a non-empty string")
    if not isinstance(path, str):
        raise ValueError("path must be a string")
    if not isinstance(query, list):
        raise ValueError("query must be a list")
    if not isinstance(headers, dict):
        raise ValueError("headers must be a dict")
    if not isinstance(options, dict):
        raise ValueError("options must be a dict")
    if not isinstance(body, (str, bytes)):
        raise ValueError("body must be str or bytes")

    ignored = options.get("ignored_headers", [])
    if not isinstance(ignored, list):
        raise ValueError("ignored_headers must be a list")
    if any(not isinstance(name, str) for name in ignored):
        raise ValueError("ignored header names must be strings")
    ignored = {name.lower() for name in ignored}

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

    normalized_headers = {}
    whitespace = re.compile(r"\s+")
    for name, value in headers.items():
        if (
            not isinstance(name, str)
            or not name
            or any(char.isspace() or ord(char) < 32 or ord(char) == 127 for char in name)
            or not isinstance(value, str)
        ):
            raise ValueError("malformed header data")
        normalized_name = name.lower()
        normalized_value = whitespace.sub(" ", value.strip())
        if normalized_name not in ignored:
            normalized_headers[normalized_name] = normalized_value

    header_string = "\n".join(
        f"{name}:{normalized_headers[name]}"
        for name in sorted(normalized_headers)
    )

    body_bytes = body.encode("utf-8") if isinstance(body, str) else body
    body_digest = hashlib.sha256(body_bytes).hexdigest()

    return "\n".join((
        method.upper(),
        path,
        query_string,
        header_string,
        body_digest,
    ))