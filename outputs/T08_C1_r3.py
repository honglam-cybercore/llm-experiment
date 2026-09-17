import re

def redact(data, sensitive_keys, sensitive_patterns):
    compiled_patterns = []
    for pattern in (sensitive_patterns or []):
        try:
            compiled_patterns.append(re.compile(pattern))
        except:
            pass
    
    normalized_keys = set()
    for key in (sensitive_keys or []):
        try:
            normalized_keys.add(str(key).lower())
        except:
            pass
    
    def _redact_recursive(obj):
        if isinstance(obj, dict):
            redacted_dict = {}
            for key, value in obj.items():
                key_lower = str(key).lower()
                if key_lower in normalized_keys:
                    redacted_dict[key] = "[REDACTED]"
                else:
                    redacted_dict[key] = _redact_recursive(value)
            return redacted_dict
        elif isinstance(obj, list):
            return [_redact_recursive(item) for item in obj]
        elif isinstance(obj, str):
            redacted_str = obj
            for pattern in compiled_patterns:
                try:
                    redacted_str = pattern.sub("[REDACTED]", redacted_str)
                except:
                    pass
            return redacted_str
        else:
            return obj
    
    try:
        return _redact_recursive(data)
    except:
        return data
