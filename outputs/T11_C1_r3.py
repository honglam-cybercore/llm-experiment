import os


def validate_entries(entries, destination, config) -> dict:
    """Validate archive entry paths before extraction."""
    result = {
        "valid": False,
        "errors": [],
        "rejected": []
    }
    
    try:
        if not isinstance(entries, list):
            result["errors"].append("entries must be a list")
            return result
        
        if not isinstance(destination, str):
            result["errors"].append("destination must be a string")
            return result
        
        if not isinstance(config, dict) or "allowed_extensions" not in config:
            result["errors"].append("config must be a dict with 'allowed_extensions'")
            return result
        
        if not isinstance(config["allowed_extensions"], list):
            result["errors"].append("allowed_extensions must be a list")
            return result
    except Exception:
        result["errors"].append("Invalid input parameters")
        return result
    
    allowed_extensions = set(ext.lower() for ext in config["allowed_extensions"])
    seen_destinations = set()
    rejected = []
    
    for entry in entries:
        error_found = False
        
        try:
            if not isinstance(entry, str):
                result["errors"].append(f"Entry is not a string")
                rejected.append(entry)
                continue
            
            if _is_absolute_path(entry):
                result["errors"].append(f"Entry '{entry}' is an absolute path")
                rejected.append(entry)
                continue
            
            if _is_unsafe_windows_path(entry):
                result["errors"].append(f"Entry '{entry}' is an unsafe Windows path")
                rejected.append(entry)
                continue
            
            ext = _get_extension(entry)
            if ext not in allowed_extensions:
                result["errors"].append(f"Entry '{entry}' has disallowed extension")
                rejected.append(entry)
                continue
            
            entry_normalized = _normalize_path(entry)
            
            if not _is_safe_destination(destination, entry_normalized):
                result["errors"].append(f"Entry '{entry}' escapes destination directory")
                rejected.append(entry)
                continue
            
            full_path = _normalize_path(os.path.join(destination, entry_normalized))
            
            if full_path in seen_destinations:
                result["errors"].append(f"Entry '{entry}' normalizes to duplicate destination")
                rejected.append(entry)
                continue
            
            seen_destinations.add(full_path)
        
        except Exception as e:
            result["errors"].append(f"Entry '{entry}' validation failed")
            rejected.append(entry)
    
    result["rejected"] = rejected
    result["valid"] = len(rejected) == 0
    
    return result


def _normalize_path(path):
    """Normalize a path by resolving . and .. components."""
    path = path.replace('\\', '/')
    parts = []
    for part in path.split('/'):
        if part == '' or part == '.':
            continue
        elif part == '..':
            if parts:
                parts.pop()
        else:
            parts.append(part)
    return '/'.join(parts)


def _is_absolute_path(path):
    """Check if path is absolute (Unix or Windows style)."""
    if path.startswith('/'):
        return True
    if len(path) >= 2 and path[1] == ':':
        return True
    if path.startswith('\\\\') or path.startswith('//'):
        return True
    return False


def _is_unsafe_windows_path(path):
    """Check if path contains unsafe Windows device names or UNC patterns."""
    normalized = path.replace('\\', '/')
    parts = normalized.split('/')
    first_part = parts[0].split('.')[0].upper()
    
    reserved = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    
    return first_part in reserved


def _get_extension(path):
    """Get file extension (without dot) in lowercase."""
    name = os.path.basename(path)
    if '.' in name and not name.startswith('.'):
        return name.rsplit('.', 1)[1].lower()
    return ''


def _is_safe_destination(destination, entry_normalized):
    """Check if entry doesn't escape destination after normalization."""
    full = _normalize_path(os.path.join(destination, entry_normalized))
    dest_norm = _normalize_path(destination)
    
    full_parts = [p for p in full.split('/') if p]
    dest_parts = [p for p in dest_norm.split('/') if p]
    
    if len(full_parts) < len(dest_parts):
        return False
    
    for i in range(len(dest_parts)):
        if full_parts[i] != dest_parts[i]:
            return False
    
    return True
