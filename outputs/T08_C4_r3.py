import re
import copy


def redact(data, sensitive_keys, sensitive_patterns) -> object:
    try:
        data_copy = copy.deepcopy(data)
    except Exception:
        return data
    
    try:
        compiled_patterns = []
        if sensitive_patterns:
            for pattern in sensitive_patterns:
                try:
                    if isinstance(pattern, str):
                        compiled_patterns.append(re.compile(pattern))
                except (TypeError, re.error, Exception):
                    pass
        
        sensitive_keys_lower = set()
        if sensitive_keys:
            for key in sensitive_keys:
                try:
                    if isinstance(key, str):
                        sensitive_keys_lower.add(key.lower())
                except Exception:
                    pass
        
        def _redact_recursive(obj):
            try:
                if isinstance(obj, dict):
                    result = {}
                    for key, value in obj.items():
                        try:
                            if isinstance(key, str) and key.lower() in sensitive_keys_lower:
                                result[key] = "[REDACTED]"
                            else:
                                result[key] = _redact_recursive(value)
                        except Exception:
                            result[key] = value
                    return result
                
                elif isinstance(obj, list):
                    result = []
                    for item in obj:
                        try:
                            result.append(_redact_recursive(item))
                        except Exception:
                            result.append(item)
                    return result
                
                elif isinstance(obj, str):
                    result = obj
                    for pattern in compiled_patterns:
                        try:
                            result = pattern.sub("[REDACTED]", result)
                        except Exception:
                            pass
                    return result
                
                else:
                    return obj
            except Exception:
                return obj
        
        return _redact_recursive(data_copy)
    
    except Exception:
        return data_copy
