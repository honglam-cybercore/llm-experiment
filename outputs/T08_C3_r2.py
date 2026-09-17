import re

def redact(data, sensitive_keys, sensitive_patterns) -> object:
    # Build a set of lowercase sensitive keys for case-insensitive comparison
    sensitive_keys_lower = set()
    try:
        if sensitive_keys:
            for key in sensitive_keys:
                if isinstance(key, str):
                    sensitive_keys_lower.add(key.lower())
    except (TypeError, AttributeError):
        pass
    
    # Compile regex patterns
    compiled_patterns = []
    try:
        if sensitive_patterns:
            for pattern in sensitive_patterns:
                try:
                    if isinstance(pattern, str):
                        compiled_patterns.append(re.compile(pattern))
                except re.error:
                    pass
    except TypeError:
        pass
    
    def redact_recursive(value, depth=0):
        """Recursively redact sensitive information."""
        try:
            # Limit recursion depth to prevent stack overflow
            if depth > 1000:
                return value
            
            # Handle None, bool, numbers
            if value is None or isinstance(value, bool):
                return value
            
            if isinstance(value, (int, float)):
                return value
            
            # Handle strings - apply regex patterns
            if isinstance(value, str):
                result = value
                for pattern in compiled_patterns:
                    try:
                        result = pattern.sub("[REDACTED]", result)
                    except (TypeError, AttributeError):
                        pass
                return result
            
            # Handle dictionaries
            if isinstance(value, dict):
                new_dict = {}
                try:
                    for key, val in value.items():
                        if isinstance(key, str) and key.lower() in sensitive_keys_lower:
                            new_dict[key] = "[REDACTED]"
                        else:
                            new_dict[key] = redact_recursive(val, depth + 1)
                except (TypeError, AttributeError):
                    return value
                return new_dict
            
            # Handle lists
            if isinstance(value, list):
                new_list = []
                try:
                    for item in value:
                        new_list.append(redact_recursive(item, depth + 1))
                except (TypeError, AttributeError):
                    return value
                return new_list
            
            # Return unchanged for other types
            return value
        except Exception:
            return value
    
    try:
        return redact_recursive(data)
    except Exception:
        return data
