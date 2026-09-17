import re

def redact(data, sensitive_keys, sensitive_patterns) -> object:
    # Convert sensitive_keys to lowercase for case-insensitive comparison
    sensitive_keys_lower = {key.lower() for key in sensitive_keys if isinstance(key, str)}
    
    # Compile regex patterns, handle errors gracefully
    compiled_patterns = []
    for pattern in sensitive_patterns:
        try:
            compiled_patterns.append(re.compile(pattern))
        except:
            pass
    
    def redact_value(value):
        """Recursively redact a value"""
        try:
            if isinstance(value, dict):
                result = {}
                for key, val in value.items():
                    # Check if key is sensitive (case-insensitive)
                    if isinstance(key, str) and key.lower() in sensitive_keys_lower:
                        result[key] = "[REDACTED]"
                    else:
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
        except:
            return value
    
    try:
        return redact_value(data)
    except:
        return data
