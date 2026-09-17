import os

def validate_entries(entries, destination, config) -> dict:
    result = {"valid": True, "errors": [], "rejected": []}
    
    # Input validation
    if not isinstance(entries, list):
        result["valid"] = False
        result["errors"].append("entries must be a list")
        return result
    
    if not isinstance(destination, str):
        result["valid"] = False
        result["errors"].append("destination must be a string")
        return result
    
    if not isinstance(config, dict) or "allowed_extensions" not in config:
        result["valid"] = False
        result["errors"].append("config must be dict with 'allowed_extensions'")
        return result
    
    if not isinstance(config["allowed_extensions"], list):
        result["valid"] = False
        result["errors"].append("allowed_extensions must be list")
        return result
    
    allowed_ext = set(e.lower() for e in config["allowed_extensions"])
    seen_destinations = {}
    
    for entry in entries:
        error_msg = _validate_entry(entry, destination, allowed_ext, seen_destinations)
        if error_msg:
            result["valid"] = False
            result["errors"].append(error_msg)
            result["rejected"].append(entry)
    
    return result


def _validate_entry(entry, destination, allowed_ext, seen_destinations):
    """Validate a single entry. Returns error message or None."""
    
    if not isinstance(entry, str):
        return f"{entry}: not a string"
    
    # Check for absolute POSIX path
    if entry.startswith('/'):
        return f"{entry}: absolute POSIX path"
    
    # Check for Windows drive letter path
    if len(entry) >= 2 and entry[1] == ':':
        return f"{entry}: Windows drive path"
    
    # Check for UNC path
    if entry.startswith('\\\\'):
        return f"{entry}: UNC path"
    
    # Check for mixed path separators
    if '/' in entry and '\\' in entry:
        return f"{entry}: mixed path separators"
    
    # Check for reserved Windows device names
    first_component = entry.replace('\\', '/').split('/')[0].upper()
    if first_component in {'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4',
                           'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3',
                           'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'}:
        return f"{entry}: reserved device name"
    
    # Normalize entry path
    normalized_entry = _normalize_path(entry)
    
    # Normalize destination
    normalized_dest = _normalize_path(destination.replace('\\', '/'))
    
    # Compute full path
    if normalized_dest:
        full_path = _normalize_path(normalized_dest + '/' + normalized_entry)
    else:
        full_path = normalized_entry
    
    # Check for escape attempt (starts with ..)
    if full_path.startswith('..'):
        return f"{entry}: path escapes destination"
    
    # Verify path is contained within destination
    if normalized_dest:
        is_contained = (full_path == normalized_dest or 
                       full_path.startswith(normalized_dest + '/'))
    else:
        is_contained = True
    
    if not is_contained:
        return f"{entry}: path escapes destination"
    
    # Check file extension
    _, ext = os.path.splitext(entry)
    ext_lower = ext.lstrip('.').lower() if ext else ''
    
    if ext_lower not in allowed_ext:
        return f"{entry}: extension not allowed"
    
    # Check for duplicate destinations
    if full_path in seen_destinations:
        return f"{entry}: duplicate destination"
    
    seen_destinations[full_path] = entry
    return None


def _normalize_path(path):
    """Normalize path by resolving . and .. components."""
    if not path:
        return ''
    
    parts = []
    for segment in path.split('/'):
        if not segment or segment == '.':
            continue
        elif segment == '..':
            if parts:
                parts.pop()
            else:
                parts.append('..')
        else:
            parts.append(segment)
    
    return '/'.join(parts)
