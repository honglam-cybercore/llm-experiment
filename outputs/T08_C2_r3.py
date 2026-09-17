import re
from copy import deepcopy

def redact(data, sensitive_keys, sensitive_patterns):
    result = deepcopy(data)
    sensitive_keys_lower = [key.lower() for key in sensitive_keys]
    compiled_patterns = [re.compile(pattern) for pattern in sensitive_patterns]
    
    def process_value(value):
        if isinstance(value, dict):
            new_dict = {}
            for key, val in value.items():
                if key.lower() in sensitive_keys_lower:
                    new_dict[key] = "[REDACTED]"
                else:
                    new_dict[key] = process_value(val)
            return new_dict
        elif isinstance(value, list):
            return [process_value(item) for item in value]
        elif isinstance(value, str):
            result_str = value
            for pattern in compiled_patterns:
                result_str = pattern.sub("[REDACTED]", result_str)
            return result_str
        else:
            return value
    
    return process_value(result)
