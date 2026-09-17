import os


def validate_entries(entries, destination, config) -> dict:
    # Input validation
    if not isinstance(entries, list):
        return {"valid": False, "errors": ["entries must be a list"], "rejected": []}
    if not isinstance(destination, str):
        return {"valid": False, "errors": ["destination must be a string"], "rejected": []}
    if not isinstance(config, dict) or "allowed_extensions" not in config:
        return {"valid": False, "errors": ["invalid config"], "rejected": []}
    
    try:
        allowed_exts = {ext.lower() for ext in config["allowed_extensions"]}
        dest_norm = os.path.normpath(os.path.abspath(destination))
    except:
        return {"valid": False, "errors": ["invalid input"], "rejected": []}
    
    reserved = {'CON', 'PRN', 'AUX', 'NUL'} | {f'COM{i}' for i in range(1, 10)} | {f'LPT{i}' for i in range(1, 10)}
    
    errors = []
    rejected = []
    seen = {}
    
    for entry in entries:
        if not isinstance(entry, str):
            errors.append(f"not a string")
            rejected.append(entry)
            continue
        
        reasons = []
        
        # Check for absolute POSIX path
        if entry.startswith('/'):
            reasons.append("absolute path")
        # Check for Windows drive letter
        elif len(entry) >= 2 and entry[1] == ':':
            reasons.append("Windows drive")
        # Check for UNC path
        elif entry.startswith('//') or entry.startswith('\\\\'):
            reasons.append("UNC path")
        
        # Check for parent directory traversal
        if '..' in entry:
            reasons.append("parent traversal")
        
        # Check for unsafe mixed separators
        if '\\' in entry and '/' in entry:
            reasons.append("mixed separators")
        
        if reasons:
            for r in reasons:
                errors.append(f"{entry}: {r}")
            rejected.append(entry)
            continue
        
        try:
            # Normalize path separators and remove empty/dot components
            norm = entry.replace('\\', '/')
            parts = [p for p in norm.split('/') if p and p != '.']
            normalized_path = '/'.join(parts)
            
            # Check for reserved device names
            for part in parts:
                if part.split('.')[0].upper() in reserved:
                    reasons.append("reserved name")
                    break
            
            if reasons:
                for r in reasons:
                    errors.append(f"{entry}: {r}")
                rejected.append(entry)
                continue
            
            # Check file extension
            _, ext = os.path.splitext(normalized_path)
            if ext:
                if ext[1:].lower() not in allowed_exts:
                    reasons.append("extension not allowed")
            elif allowed_exts:
                reasons.append("no extension")
            
            if reasons:
                for r in reasons:
                    errors.append(f"{entry}: {r}")
                rejected.append(entry)
                continue
            
            # Build full path and check for destination escape
            full = os.path.join(dest_norm, normalized_path.replace('/', os.sep))
            full = os.path.normpath(os.path.abspath(full))
            
            try:
                rel = os.path.relpath(full, dest_norm)
                if rel.startswith('..') or os.path.isabs(rel):
                    reasons.append("escapes destination")
            except:
                reasons.append("escapes destination")
            
            if reasons:
                for r in reasons:
                    errors.append(f"{entry}: {r}")
                rejected.append(entry)
                continue
            
            # Check for duplicate destinations
            if full in seen:
                errors.append(f"{entry}: duplicate destination")
                rejected.append(entry)
            else:
                seen[full] = entry
        
        except:
            errors.append(f"{entry}: processing error")
            rejected.append(entry)
    
    return {"valid": len(rejected) == 0, "errors": errors, "rejected": rejected}
