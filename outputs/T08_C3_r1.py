import re

def redact(data, sensitive_keys, sensitive_patterns) -> object:
    # Ensure we have lists
    if not isinstance(sensitive_keys, (list, tuple)):
        sensitive_keys = []
    if not isinstance(sensitive_patterns, (list, tuple)):
        sensitive_patterns = []
    
    # Compile patterns
    compiled_patterns = []
    for pattern in sensitive_patterns:
        try:
            if isinstance(pattern, str):
                compiled_patterns.append(re.compile(pattern))
        except Exception:
            pass
    
    # Normalize keys
    normalized_keys = set()
    for key in sensitive_keys:
        if isinstance(key, str):
            normalized_keys.add(key.lower())
    
    def redact_value(value):
        if isinstance(value, str):
            for pattern in compiled_patterns:
                try:
                    value = pattern.sub("[REDACTED]", value)
                except Exception:
                    pass
        return value
    
    def process(obj):
        try:
            if isinstance(obj, dict):
                result_dict = {}
                for key, value in obj.items():
                    key_lower = key.lower() if isinstance(key, str) else None
                    if key_lower in normalized_keys:
                        result_dict[key] = "[REDACTED]"
                    elif isinstance(value, (dict, list)):
                        result_dict[key] = process(value)
                    else:
                        result_dict[key] = redact_value(value)
                return result_dict
            elif isinstance(obj, list):
                result_list = []
                for item in obj:
                    if isinstance(item, (dict, list)):
                        result_list.append(process(item))
                    else:
                        result_list.append(redact_value(item))
                return result_list
            else:
                return redact_value(obj)
        except Exception:
            return obj
    
    try:
        return process(data)
    except Exception:
        return data
