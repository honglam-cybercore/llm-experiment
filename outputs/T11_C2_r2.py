import os

def validate_entries(entries, destination, config) -> dict:
    errors = []
    rejected = []
    
    # Validate input types
    if not isinstance(entries, list):
        return {"valid": False, "errors": ["entries must be a list"], "rejected": []}
    
    if not isinstance(destination, str):
        return {"valid": False, "errors": ["destination must be a string"], "rejected": []}
    
    if not isinstance(config, dict) or "allowed_extensions" not in config:
        return {"valid": False, "errors": ["config must be a dict with 'allowed_extensions'"], "rejected": []}
    
    allowed_extensions = config.get("allowed_extensions", [])
    if not isinstance(allowed_extensions, list):
        return {"valid": False, "errors": ["allowed_extensions must be a list"], "rejected": []}
    
    # Normalize allowed extensions to lowercase
    allowed_extensions_lower = set(ext.lower() for ext in allowed_extensions)
    
    # Normalize destination path
    try:
        dest_path = os.path.normpath(destination)
        dest_abs = os.path.abspath(dest_path)
    except (TypeError, ValueError):
        return {"valid": False, "errors": ["destination path is invalid"], "rejected": []}
    
    seen_destinations = set()
    reserved_names = {'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'}
    
    for entry in entries:
        # Check if entry is a string
        if not isinstance(entry, str):
            errors.append("Entry is not a string")
            rejected.append(entry)
            continue
        
        # Check for empty entry
        if not entry:
            errors.append("Entry is empty")
            rejected.append(entry)
            continue
        
        # Check for absolute POSIX paths
        if entry.startswith('/'):
            errors.append(f"Entry is an absolute path: {entry}")
            rejected.append(entry)
            continue
        
        # Check for Windows drive paths
        if len(entry) >= 2 and entry[1] == ':' and entry[0].isalpha():
            errors.append(f"Entry is a Windows drive path: {entry}")
            rejected.append(entry)
            continue
        
        # Check for UNC paths
        if entry.startswith('\\\\') or entry.startswith('//'):
            errors.append(f"Entry is a UNC path: {entry}")
            rejected.append(entry)
            continue
        
        # Check for mixed separators
        if '\\' in entry and '/' in entry:
            errors.append(f"Entry has mixed separators: {entry}")
            rejected.append(entry)
            continue
        
        # Normalize separators for path analysis
        normalized_entry = entry.replace('\\', '/')
        
        # Check for parent directory traversal
        parts = normalized_entry.split('/')
        if '..' in parts:
            errors.append(f"Entry contains parent directory traversal: {entry}")
            rejected.append(entry)
            continue
        
        # Check for reserved device names
        first_component = parts[0].split('.')[0].upper() if parts[0] else ""
        if first_component in reserved_names:
            errors.append(f"Entry uses reserved device name: {entry}")
            rejected.append(entry)
            continue
        
        # Check file extension
        _, ext = os.path.splitext(entry)
        if ext:
            ext_str = ext.lstrip('.').lower()
        else:
            ext_str = ''
        
        if ext_str not in allowed_extensions_lower:
            errors.append(f"Entry has disallowed extension: {entry}")
            rejected.append(entry)
            continue
        
        # Normalize and check path
        try:
            full_path = os.path.normpath(os.path.join(dest_path, normalized_entry))
            full_path_abs = os.path.abspath(full_path)
        except (TypeError, ValueError):
            errors.append(f"Entry path cannot be normalized: {entry}")
            rejected.append(entry)
            continue
        
        # Check if path stays within destination
        try:
            rel_path = os.path.relpath(full_path_abs, dest_abs)
            if rel_path.startswith('..'):
                errors.append(f"Entry escapes destination: {entry}")
                rejected.append(entry)
                continue
        except ValueError:
            errors.append(f"Entry escapes destination: {entry}")
            rejected.append(entry)
            continue
        
        # Check for duplicate destinations
        if full_path_abs in seen_destinations:
            errors.append(f"Entry resolves to duplicate destination: {entry}")
            rejected.append(entry)
            continue
        
        seen_destinations.add(full_path_abs)
    
    valid = len(rejected) == 0
    return {"valid": valid, "errors": errors, "rejected": rejected}
