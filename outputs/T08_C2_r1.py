import re

def redact(data, sensitive_keys, sensitive_patterns) -> object:
    try:
        # Convert sensitive keys to lowercase for case-insensitive matching
        sensitive_keys_lower = [str(key).lower() for key in (sensitive_keys or [])]
        
        # Compile regex patterns for efficiency
        compiled_patterns = []
        for pattern in (sensitive_patterns or []):
            try:
                compiled_patterns.append(re.compile(pattern))
            except Exception:
                pass
        
        def redact_recursive(obj):
            if isinstance(obj, dict):
                result = {}
                for key, value in obj.items():
                    if str(key).lower() in sensitive_keys_lower:
                        result[key] = "[REDACTED]"
                    else:
                        result[key] = redact_recursive(value)
                return result
            elif isinstance(obj, list):
                return [redact_recursive(item) for item in obj]
            elif isinstance(obj, str):
                result = obj
                for pattern in compiled_patterns:
                    result = pattern.sub("[REDACTED]", result)
                return result
            else:
                # For numbers, booleans, None - return as is
                return obj
        
        return redact_recursive(data)
    except Exception:
        # Never raise - return original data if something goes wrong
        return data
