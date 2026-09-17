import os


def validate_entries(entries, destination, config) -> dict:
    """Validate archive entry paths before extraction."""
    
    result = {
        "valid": True,
        "errors": [],
        "rejected": []
    }
    
    # Validate input types
    try:
        if not isinstance(entries, list):
            result["valid"] = False
            result["errors"].append("entries must be a list")
            return result
        
        if not isinstance(destination, str) or not destination:
            result["valid"] = False
            result["errors"].append("destination must be a non-empty string")
            return result
        
        if not isinstance(config, dict):
            result["valid"] = False
            result["errors"].append("config must be a dict")
            return result
        
        if "allowed_extensions" not in config:
            result["valid"] = False
            result["errors"].append("config must contain allowed_extensions")
            return result
        
        allowed_extensions = config["allowed_extensions"]
        if not isinstance(allowed_extensions, list):
            result["valid"] = False
            result["errors"].append("allowed_extensions must be a list")
            return result
    except Exception:
        result["valid"] = False
        result["errors"].append("Invalid input")
        return result
    
    # Normalize allowed extensions to lowercase for case-insensitive matching
    allowed_ext_lower = set(ext.lower() for ext in allowed_extensions)
    
    # Normalize destination path
    dest_normalized = _normalize_path(destination)
    
    # Track normalized paths to detect duplicates
    seen_normalized = {}
    
    # Process each entry
    for entry in entries:
        if not isinstance(entry, str):
            result["valid"] = False
            result["errors"].append("Entry must be a string")
            result["rejected"].append(str(entry))
            continue
        
        # Check if path is absolute
        if os.path.isabs(entry):
            result["valid"] = False
            result["errors"].append(f"{entry}: Absolute path not allowed")
            result["rejected"].append(entry)
            continue
        
        # Check for unsafe Windows paths
        if _is_unsafe_windows_path(entry):
            result["valid"] = False
            result["errors"].append(f"{entry}: Unsafe Windows path")
            result["rejected"].append(entry)
            continue
        
        # Normalize entry path
        try:
            normalized_entry = _normalize_path(entry)
        except Exception:
            result["valid"] = False
            result["errors"].append(f"{entry}: Invalid path")
            result["rejected"].append(entry)
            continue
        
        # Join with destination
        final_path = _safe_join(dest_normalized, normalized_entry)
        
        # Check if path escapes destination
        if not _is_within_directory(final_path, dest_normalized):
            result["valid"] = False
            result["errors"].append(f"{entry}: Path escapes destination")
            result["rejected"].append(entry)
            continue
        
        # Check file extension
        _, ext = os.path.splitext(entry)
        if ext.startswith('.'):
            ext = ext[1:]
        
        if not ext or ext.lower() not in allowed_ext_lower:
            result["valid"] = False
            result["errors"].append(f"{entry}: Extension not allowed")
            result["rejected"].append(entry)
            continue
        
        # Check for duplicate normalized destinations
        normalized_key = final_path.lower()
        if normalized_key in seen_normalized:
            result["valid"] = False
            result["errors"].append(f"{entry}: Duplicate destination")
            result["rejected"].append(entry)
            continue
        
        seen_normalized[normalized_key] = entry
    
    return result


def _normalize_path(path: str) -> str:
    """Normalize path by resolving . and .. components."""
    path = path.replace('\\', '/')
    
    parts = []
    for component in path.split('/'):
        if component == '' or component == '.':
            continue
        elif component == '..':
            if parts:
                parts.pop()
        else:
            parts.append(component)
    
    return '/'.join(parts)


def _is_unsafe_windows_path(path: str) -> bool:
    """Check if path contains unsafe Windows elements."""
    # Check for drive letter
    if len(path) >= 2 and path[1] == ':':
        return True
    
    # Check for UNC path
    if path.startswith('\\\\') or path.startswith('//'):
        return True
    
    # Check for reserved device names
    reserved = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    
    first = path.split('/')[0].split('\\')[0]
    base = first.split('.')[0].upper()
    
    return base in reserved


def _safe_join(base: str, relative: str) -> str:
    """Join base and relative paths, resolving .. references."""
    parts = []
    
    for component in base.split('/'):
        if component and component != '.':
            parts.append(component)
    
    for component in relative.split('/'):
        if component == '' or component == '.':
            continue
        elif component == '..':
            if parts:
                parts.pop()
        else:
            parts.append(component)
    
    return '/'.join(parts)


def _is_within_directory(path: str, directory: str) -> str:
    """Check if path is within directory."""
    if not directory:
        return True
    
    if path == directory:
        return True
    
    if path.startswith(directory + '/'):
        return True
    
    return False
