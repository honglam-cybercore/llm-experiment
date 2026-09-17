import re
import copy

def redact(data, sensitive_keys, sensitive_patterns) -> object:
    try:
        data_copy = copy.deepcopy(data)
    except:
        return data
    
    sensitive_keys_lower = set()
    try:
        for key in sensitive_keys or []:
            if isinstance(key, str):
                sensitive_keys_lower.add(key.lower())
    except:
        pass
    
    compiled_patterns = []
    try:
        for pattern in sensitive_patterns or []:
            try:
                if isinstance(pattern, str):
                    compiled_patterns.append(re.compile(pattern))
            except:
                pass
    except:
        pass
    
    def redact_recursive(obj):
        try:
            if isinstance(obj, dict):
                result = {}
                for key, value in obj.items():
                    key_lower = key.lower() if isinstance(key, str) else key
                    if key_lower in sensitive_keys_lower:
                        result[key] = "[REDACTED]"
                    else:
                        result[key] = redact_recursive(value)
                return result
            elif isinstance(obj, list):
                return [redact_recursive(item) for item in obj]
            elif isinstance(obj, str):
                result = obj
                for pattern in compiled_patterns:
                    try:
                        result = pattern.sub("[REDACTED]", result)
                    except:
                        pass
                return result
            else:
                return obj
        except:
            return obj
    
    try:
        return redact_recursive(data_copy)
    except:
        return data_copy
