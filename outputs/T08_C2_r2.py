import re

def redact(data, sensitive_keys, sensitive_patterns) -> object:
    # Convert sensitive_keys to lowercase for case-insensitive comparison
    sensitive_keys_lower = {key.lower() for key in (sensitive_keys or [])}
    
    # Compile patterns once for efficiency
    compiled_patterns = []
    for pattern in (sensitive_patterns or []):
        try:
            compiled_patterns.append(re.compile(pattern))
        except:
            pass
    
    def redact_value(value, is_sensitive_key=False):
        # If this value is under a sensitive key, redact the whole thing
        if is_sensitive_key:
            return "[REDACTED]"
        
        # Handle different types
        if isinstance(value, dict):
            result = {}
            for k, v in value.items():
                # Check if key is sensitive (case-insensitive)
                key_is_sensitive = str(k).lower() in sensitive_keys_lower
                result[k] = redact_value(v, key_is_sensitive)
            return result
        
        elif isinstance(value, list):
            return [redact_value(item, False) for item in value]
        
        elif isinstance(value, str):
            # Apply pattern redactions
            result = value
            for pattern in compiled_patterns:
                result = pattern.sub("[REDACTED]", result)
            return result
        
        else:
            # Numbers, booleans, None - return as is
            return value
    
    return redact_value(data, False)
