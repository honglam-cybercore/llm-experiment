import re

def redact(data, sensitive_keys, sensitive_patterns) -> object:
    try:
        # Normalize sensitive keys to lowercase for case-insensitive comparison
        sensitive_keys_lower = set()
        if sensitive_keys:
            for k in sensitive_keys:
                try:
                    key_str = k.lower() if isinstance(k, str) else str(k).lower()
                    sensitive_keys_lower.add(key_str)
                except Exception:
                    pass
        
        # Compile regex patterns, skip invalid ones
        compiled_patterns = []
        if sensitive_patterns:
            for pattern in sensitive_patterns:
                try:
                    compiled_patterns.append(re.compile(pattern))
                except Exception:
                    continue
        
        def _redact_value(value):
            try:
                if isinstance(value, dict):
                    result = {}
                    for k, v in value.items():
                        try:
                            key_str = k.lower() if isinstance(k, str) else str(k).lower()
                            if key_str in sensitive_keys_lower:
                                result[k] = "[REDACTED]"
                            else:
                                result[k] = _redact_value(v)
                        except Exception:
                            result[k] = v
                    return result
                elif isinstance(value, list):
                    result = []
                    for item in value:
                        try:
                            result.append(_redact_value(item))
                        except Exception:
                            result.append(item)
                    return result
                elif isinstance(value, str):
                    result = value
                    for pattern in compiled_patterns:
                        try:
                            result = pattern.sub("[REDACTED]", result)
                        except Exception:
                            continue
                    return result
                else:
                    return value
            except Exception:
                return value
        
        return _redact_value(data)
    except Exception:
        return data
