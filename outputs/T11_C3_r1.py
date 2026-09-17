import os


def validate_entries(entries, destination, config) -> dict:
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
        result["errors"].append("config must contain 'allowed_extensions'")
        return result
    
    allowed_exts = config["allowed_extensions"]
    if not isinstance(allowed_exts, list):
        result["errors"].append("allowed_extensions must be a list")
        return result
    
    # Normalize allowed extensions (lowercase, remove leading dot)
    allowed_extensions = set()
    for ext in allowed_exts:
        try:
            ext_clean = str(ext).lower().lstrip('.')
            allowed_extensions.add(ext_clean)
        except Exception:
            result["errors"].append(f"cannot process extension: {repr(ext)}")
            return result
    
    # Get absolute destination path
    try:
        dest_abs = os.path.abspath(destination)
    except Exception:
        result["errors"].append("cannot process destination path")
        return result
    
    # For path containment check
    if not dest_abs.endswith(os.sep):
        dest_sep = dest_abs + os.sep
    else:
        dest_sep = dest_abs
    
    # Track normalized paths for duplicate detection
    seen_paths = {}
    
    # Windows reserved device names
    reserved = {
        'con', 'prn', 'aux', 'nul',
        'com1', 'com2', 'com3', 'com4', 'com5', 'com6', 'com7', 'com8', 'com9',
        'lpt1', 'lpt2', 'lpt3', 'lpt4', 'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9'
    }
    
    for entry in entries:
        # Entry must be a string
        if not isinstance(entry, str):
            result["errors"].append(f"entry is not a string")
            result["rejected"].append(entry if isinstance(entry, str) else "")
            continue
        
        is_valid = True
        
        # Check: Absolute path
        if os.path.isabs(entry):
            result["errors"].append(f"absolute path: {entry}")
            is_valid = False
        
        # Check: Windows drive letter (e.g., C:)
        elif len(entry) >= 2 and entry[1] == ':':
            result["errors"].append(f"drive letter: {entry}")
            is_valid = False
        
        # Check: UNC path
        elif entry.startswith('\\\\') or entry.startswith('//'):
            result["errors"].append(f"UNC path: {entry}")
            is_valid = False
        
        # Check: Reserved device names
        if is_valid:
            parts = entry.replace('\\', '/').split('/')
            for part in parts:
                if part:
                    # Remove Windows reserved suffix (trailing dots/colons)
                    clean = part.rstrip('. :').lower()
                    if clean in reserved:
                        result["errors"].append(f"reserved name: {entry}")
                        is_valid = False
                        break
        
        # Check path normalization and containment
        if is_valid:
            entry_os = entry.replace('/', os.sep).replace('\\', os.sep)
            joined = os.path.join(dest_abs, entry_os)
            final_path = os.path.abspath(joined)
            
            # Path must be within destination
            if not (final_path == dest_abs or final_path.startswith(dest_sep)):
                result["errors"].append(f"escapes destination: {entry}")
                is_valid = False
            
            # Check extension
            if is_valid:
                _, ext = os.path.splitext(entry)
                ext_lower = ext.lower().lstrip('.') if ext else ''
                
                if ext_lower not in allowed_extensions:
                    result["errors"].append(f"extension not allowed: {entry}")
                    is_valid = False
            
            # Check for duplicate normalized paths
            if is_valid:
                if final_path in seen_paths:
                    result["errors"].append(f"duplicate path: {entry}")
                    is_valid = False
                else:
                    seen_paths[final_path] = entry
        
        if not is_valid:
            result["rejected"].append(entry)
    
    result["valid"] = len(result["rejected"]) == 0
    
    return result
