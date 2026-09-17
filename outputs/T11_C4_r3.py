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
        result["errors"].append("config missing 'allowed_extensions'")
        return result
    
    if not isinstance(config["allowed_extensions"], list):
        result["errors"].append("allowed_extensions must be a list")
        return result
    
    # Build set of allowed extensions (lowercase)
    allowed_exts = set()
    for ext in config["allowed_extensions"]:
        if isinstance(ext, str):
            allowed_exts.add(ext.lower())
    
    # Normalize and verify destination path
    try:
        dest_abs = os.path.abspath(os.path.normpath(destination))
    except Exception:
        result["errors"].append("Invalid destination path")
        return result
    
    # Reserved Windows device names
    reserved = {'con', 'prn', 'aux', 'nul', 'com1', 'com2', 'com3', 'com4', 'com5', 'com6', 'com7', 'com8', 'com9', 'lpt1', 'lpt2', 'lpt3', 'lpt4', 'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9'}
    
    # Track seen normalized paths to detect duplicates
    seen_paths = {}
    
    # Validate each entry
    for entry in entries:
        # Check if entry is a string
        if not isinstance(entry, str):
            result["rejected"].append(str(entry))
            result["errors"].append("Entry is not a string")
            continue
        
        # Check for absolute paths
        if os.path.isabs(entry):
            result["rejected"].append(entry)
            result["errors"].append(f"Absolute path: {entry}")
            continue
        
        # Check for UNC paths (Windows network paths)
        if entry.startswith('\\\\') or entry.startswith('//'):
            result["rejected"].append(entry)
            result["errors"].append(f"UNC path: {entry}")
            continue
        
        # Check for Windows drive letter paths
        if len(entry) >= 2 and entry[1] == ':':
            result["rejected"].append(entry)
            result["errors"].append(f"Drive path: {entry}")
            continue
        
        # Check for mixed path separators
        if '/' in entry and '\\' in entry:
            result["rejected"].append(entry)
            result["errors"].append(f"Mixed separators: {entry}")
            continue
        
        # Normalize separators to forward slashes
        entry_normalized = entry.replace('\\', '/')
        
        # Check for parent directory traversal
        parts = entry_normalized.split('/')
        if '..' in parts:
            result["rejected"].append(entry)
            result["errors"].append(f"Parent directory traversal: {entry}")
            continue
        
        # Check for reserved Windows device names
        has_reserved = False
        for part in parts:
            if part and part.lower() in reserved:
                result["rejected"].append(entry)
                result["errors"].append(f"Reserved device name: {entry}")
                has_reserved = True
                break
        
        if has_reserved:
            continue
        
        # Check file extension
        _, ext = os.path.splitext(entry_normalized)
        if not ext:
            result["rejected"].append(entry)
            result["errors"].append(f"No file extension: {entry}")
            continue
        
        ext_lower = ext[1:].lower()  # Remove the leading dot
        if ext_lower not in allowed_exts:
            result["rejected"].append(entry)
            result["errors"].append(f"Extension not allowed: {entry}")
            continue
        
        # Build the full path
        try:
            full_path = os.path.join(dest_abs, entry_normalized.replace('/', os.sep))
            full_path = os.path.abspath(os.path.normpath(full_path))
            
            # Verify the path remains inside the destination
            try:
                rel_path = os.path.relpath(full_path, dest_abs)
                if rel_path.startswith('..'):
                    result["rejected"].append(entry)
                    result["errors"].append(f"Path escapes destination: {entry}")
                    continue
            except ValueError:
                result["rejected"].append(entry)
                result["errors"].append(f"Path escapes destination: {entry}")
                continue
            
            # Check for duplicate destinations
            path_key = full_path.lower() if os.name == 'nt' else full_path
            
            if path_key in seen_paths:
                result["rejected"].append(entry)
                result["errors"].append(f"Duplicate destination: {entry}")
                continue
            
            seen_paths[path_key] = entry
            
        except Exception:
            result["rejected"].append(entry)
            result["errors"].append(f"Error validating path: {entry}")
            continue
    
    result["valid"] = len(result["rejected"]) == 0
    
    return result
