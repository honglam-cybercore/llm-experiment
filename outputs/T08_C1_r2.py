import re

def redact(data, sensitive_keys, sensitive_patterns) -> object:
    # Compile patterns once, handling invalid patterns gracefully
    compiled_patterns = []
    if sensitive_patterns:
        for pattern in sensitive_patterns:
            try:
                compiled_patterns.append(re.compile(pattern))
            except:
                pass
    
    # Convert sensitive keys to lowercase set for case-insensitive matching
    sensitive_keys_lower = set()
    if sensitive_keys:
        sensitive_keys_lower = {str(key).lower() for key in sensitive_keys}
    
    def redact_recursive(obj):
        if isinstance(obj, dict):
            new_dict = {}
            for key, value in obj.items():
                # Check if key matches a sensitive key (case-insensitive)
                if str(key).lower() in sensitive_keys_lower:
                    new_dict[key] = "[REDACTED]"
                else:
                    new_dict[key] = redact_recursive(value)
            return new_dict
        elif isinstance(obj, list):
            return [redact_recursive(item) for item in obj]
        elif isinstance(obj, str):
            # Apply regex patterns to the string
            result_str = obj
            for pattern in compiled_patterns:
                try:
                    result_str = pattern.sub("[REDACTED]", result_str)
                except:
                    pass
            return result_str
        else:
            # Numbers, booleans, None - return unchanged
            return obj
    
    try:
        return redact_recursive(data)
    except:
        return data
