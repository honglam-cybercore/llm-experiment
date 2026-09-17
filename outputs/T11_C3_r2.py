import os
from pathlib import Path


def validate_entries(entries, destination, config) -> dict:
    """
    Validate archive entry paths before extraction.
    """
    result = {
        "valid": False,
        "errors": [],
        "rejected": []
    }
    
    # Input validation
    if not isinstance(entries, list):
        result["errors"].append("entries must be a list")
        return result
    
    if not isinstance(destination, str):
        result["errors"].append("destination must be a string")
        return result
    
    if not isinstance(config, dict):
        result["errors"].append("config must be a dict")
        return result
    
    if "allowed_extensions" not in config:
        result["errors"].append("config missing 'allowed_extensions' key")
        return result
    
    if not isinstance(config["allowed_extensions"], list):
        result["errors"].append("'allowed_extensions' must be a list")
        return result
    
    # Build allowed extensions set
    try:
        allowed_extensions = set(str(ext).lower() for ext in config["allowed_extensions"])
    except Exception:
        result["errors"].append("invalid extension in config")
        return result
    
    # Resolve destination path
    try:
        dest_path = Path(destination).resolve()
    except Exception:
        result["errors"].append("invalid destination path")
        return result
    
    # Reserved Windows device names
    reserved_names = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    
    seen_paths = {}
    
    for entry in entries:
        # Must be a string
        if not isinstance(entry, str):
            result["rejected"].append(str(entry))
            result["errors"].append("entry must be string")
            continue
        
        # Check for absolute paths
        if os.path.isabs(entry):
            result["rejected"].append(entry)
            result["errors"].append("absolute path")
            continue
        
        # Check for Windows UNC paths
        if entry.startswith('\\\\') or entry.startswith('//'):
            result["rejected"].append(entry)
            result["errors"].append("UNC path")
            continue
        
        # Check for drive letters
        if len(entry) >= 2 and entry[1] == ':' and entry[0].isalpha():
            result["rejected"].append(entry)
            result["errors"].append("drive letter")
            continue
        
        # Normalize and parse
        normalized = entry.replace('\\', '/').lstrip('/')
        
        if not normalized:
            result["rejected"].append(entry)
            result["errors"].append("empty path")
            continue
        
        # Process path components
        parts = normalized.split('/')
        clean_parts = []
        invalid = False
        
        for part in parts:
            if not part or part == '.':
                continue
            elif part == '..':
                if not clean_parts:
                    result["rejected"].append(entry)
                    result["errors"].append("path traversal")
                    invalid = True
                    break
                clean_parts.pop()
            else:
                # Check reserved names
                base = part.split('.')[0].upper()
                if base in reserved_names:
                    result["rejected"].append(entry)
                    result["errors"].append("reserved name")
                    invalid = True
                    break
                clean_parts.append(part)
        
        if invalid:
            continue
        
        if not clean_parts:
            result["rejected"].append(entry)
            result["errors"].append("empty path")
            continue
        
        # Resolve full path
        clean = '/'.join(clean_parts)
        try:
            full = (dest_path / clean).resolve()
        except Exception:
            result["rejected"].append(entry)
            result["errors"].append("invalid path")
            continue
        
        # Check escapes destination
        try:
            full.relative_to(dest_path)
        except ValueError:
            result["rejected"].append(entry)
            result["errors"].append("path escapes")
            continue
        
        # Check extension
        if not normalized.endswith('/'):
            ext = Path(clean).suffix.lower()
            if ext:
                ext = ext[1:]
                if ext not in allowed_extensions:
                    result["rejected"].append(entry)
                    result["errors"].append("extension not allowed")
                    continue
        
        # Check duplicate
        path_str = str(full)
        if path_str in seen_paths:
            result["rejected"].append(entry)
            result["errors"].append("duplicate")
            continue
        
        seen_paths[path_str] = entry
    
    result["valid"] = len(result["rejected"]) == 0
    return result
