import os

def validate_entries(entries, destination, config) -> dict:
    result = {
        "valid": True,
        "errors": [],
        "rejected": []
    }
    
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
        result["errors"].append("config must be a dict with 'allowed_extensions'")
        return result
    
    allowed_extensions = config["allowed_extensions"]
    if not isinstance(allowed_extensions, list):
        result["valid"] = False
        result["errors"].append("allowed_extensions must be a list")
        return result
    
    allowed_ext_lower = {str(ext).lower() for ext in allowed_extensions}
    
    reserved_names = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    
    destination = os.path.normpath(destination)
    seen_normalized = {}
    
    for entry in entries:
        entry_errors = []
        entry_valid = True
        full_path = None
        
        if not isinstance(entry, str):
            result["valid"] = False
            result["rejected"].append(str(entry))
            result["errors"].append(f"Entry is not a string: {type(entry).__name__}")
            continue
        
        if '\x00' in entry:
            entry_errors.append("Null byte in path")
            entry_valid = False
        
        if entry.startswith('/'):
            entry_errors.append("Absolute POSIX path")
            entry_valid = False
        
        if len(entry) >= 2 and entry[1] == ':':
            entry_errors.append("Windows drive path")
            entry_valid = False
        
        if entry.startswith('\\\\') or entry.startswith('//'):
            entry_errors.append("UNC path")
            entry_valid = False
        
        if '\\' in entry and '/' in entry:
            entry_errors.append("Unsafe mixed separators")
            entry_valid = False
        
        normalized = entry.replace('\\', '/')
        
        if normalized.startswith('./'):
            normalized = normalized[2:]
        
        parts = normalized.split('/')
        processed_parts = []
        
        for part in parts:
            if not part or part == '.':
                continue
            
            if part == '..':
                entry_errors.append("Parent directory traversal (..)")
                entry_valid = False
                continue
            
            name_part = part.split('.')[0].upper()
            if name_part in reserved_names:
                entry_errors.append(f"Reserved device name: {part}")
                entry_valid = False
                continue
            
            processed_parts.append(part)
        
        normalized = '/'.join(processed_parts)
        
        if not normalized:
            entry_errors.append("Empty path after normalization")
            entry_valid = False
        
        if entry_valid:
            full_path = os.path.join(destination, normalized.replace('/', os.sep))
            full_path = os.path.normpath(full_path)
            
            rel_path = None
            try:
                rel_path = os.path.relpath(full_path, destination)
            except (ValueError, TypeError):
                entry_errors.append("Path escapes destination")
                entry_valid = False
            
            if rel_path and rel_path.startswith('..'):
                entry_errors.append("Path escapes destination")
                entry_valid = False
            
            if entry_valid:
                is_directory = entry.endswith('/') or entry.endswith('\\')
                if not is_directory:
                    _, ext = os.path.splitext(normalized)
                    if ext:
                        ext = ext[1:].lower()
                        if ext not in allowed_ext_lower:
                            entry_errors.append(f"Extension not allowed: {ext}")
                            entry_valid = False
                    else:
                        entry_errors.append("No file extension")
                        entry_valid = False
                
                if entry_valid and full_path:
                    if full_path in seen_normalized:
                        entry_errors.append(f"Duplicate destination (same as '{seen_normalized[full_path]}')")
                        entry_valid = False
                    else:
                        seen_normalized[full_path] = entry
        
        if not entry_valid:
            result["valid"] = False
            result["rejected"].append(entry)
            result["errors"].extend([f"Entry '{entry}': {err}" for err in entry_errors])
    
    return result
