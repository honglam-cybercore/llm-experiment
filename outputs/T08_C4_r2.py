import re
import copy

def redact(data, sensitive_keys, sensitive_patterns) -> object:
    # Normalize sensitive keys to lowercase for case-insensitive comparison
    sensitive_keys_lower = set()
    for key in (sensitive_keys or []):
        try:
            sensitive_keys_lower.add(str(key).lower())
        except:
            pass
    
    # Compile patterns for efficiency and error handling
    compiled_patterns = []
    for pattern in (sensitive_patterns or []):
        try:
            compiled_patterns.append(re.compile(pattern))
        except:
            pass
    
    def redact_value(value):
        """Recursively redact a value based on type."""
        if isinstance(value, dict):
            result = {}
            for key, val in value.items():
                try:
                    key_str = str(key)
                    if key_str.lower() in sensitive_keys_lower:
                        result[key] = "[REDACTED]"
                    else:
                        result[key] = redact_value(val)
                except:
                    result[key] = redact_value(val)
            return result
        elif isinstance(value, list):
            return [redact_value(item) for item in value]
        elif isinstance(value, str):
            result = value
            for pattern in compiled_patterns:
                try:
                    result = pattern.sub("[REDACTED]", result)
                except:
                    pass
            return result
        else:
            return value
    
    try:
        return redact_value(data)
    except:
        try:
            return copy.deepcopy(data)
        except:
            return data
