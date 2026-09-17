import os
import posixpath

def validate_entries(entries, destination, config) -> dict:
    result = {
        "valid": False,
        "errors": [],
        "rejected": []
    }
    
    # Validate input types
    try:
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
        
        allowed_extensions = config["allowed_extensions"]
        if not isinstance(allowed_extensions, list):
            result["errors"].append("allowed_extensions must be a list")
            return result
    except Exception:
        if not result["errors"]:
            result["errors"].append("Invalid input")
        return result
    
    # Normalize destination
    try:
        dest_abs = os.path.normpath(os.path.abspath(destination))
        dest_normalized = os.path.normcase(dest_abs)
    except Exception as e:
        result["errors"].append(f"Invalid destination: {str(e)}")
        return result
    
    # Process entries
    seen_paths = {}
    
    for entry in entries:
        try:
            if not isinstance(entry, str):
                result["errors"].append("Entry must be string")
                result["rejected"].append(entry)
                continue
            
            # Reject absolute paths
            if os.path.isabs(entry):
                result["errors"].append(f"Absolute path: {entry}")
                result["rejected"].append(entry)
                continue
            
            # Reject unsafe Windows paths
            if _is_unsafe_windows_path(entry):
                result["errors"].append(f"Unsafe path: {entry}")
                result["rejected"].append(entry)
                continue
            
            # Reject disallowed extensions
            if not _is_allowed_extension(entry, allowed_extensions):
                result["errors"].append(f"Extension not allowed: {entry}")
                result["rejected"].append(entry)
                continue
            
            # Normalize entry path
            norm_entry = _normalize_entry_path(entry)
            
            # Construct full path and normalize
            full_path = os.path.normpath(os.path.join(dest_abs, norm_entry))
            full_normalized = os.path.normcase(full_path)
            
            # Reject if escapes destination
            if not _is_within_destination(full_normalized, dest_normalized):
                result["errors"].append(f"Escapes destination: {entry}")
                result["rejected"].append(entry)
                continue
            
            # Reject duplicates
            if full_normalized in seen_paths:
                result["errors"].append(f"Duplicate: {entry}")
                result["rejected"].append(entry)
                continue
            
            seen_paths[full_normalized] = entry
        
        except Exception as e:
            result["errors"].append(f"Validation error: {str(e)}")
            result["rejected"].append(entry)
    
    result["valid"] = len(result["rejected"]) == 0
    return result


def _is_unsafe_windows_path(path):
    """Detect unsafe Windows paths: drive letters, UNC paths, reserved names."""
    # Drive letter (e.g., C:)
    if len(path) >= 2 and path[1] == ':' and path[0].isalpha():
        return True
    
    # UNC path (e.g., \\server or //server)
    if path.startswith('\\\\') or path.startswith('//'):
        return True
    
    # Reserved device names
    reserved = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    
    # Check first path component
    parts = path.replace('\\', '/').split('/')
    if parts and parts[0]:
        # Strip extension for device name matching
        name = parts[0].split('.')[0].upper()
        if name in reserved:
            return True
    
    return False


def _normalize_entry_path(path):
    """Normalize an archive entry path."""
    # Convert backslashes to forward slashes
    path = path.replace('\\', '/')
    
    # Remove leading slashes
    while path.startswith('/'):
        path = path[1:]
    
    # Normalize . and .. components
    path = posixpath.normpath(path)
    
    return path


def _is_allowed_extension(path, allowed_extensions):
    """Check if file extension is in allowed list (case-insensitive)."""
    if not allowed_extensions:
        return False
    
    _, ext = os.path.splitext(path)
    if ext.startswith('.'):
        ext = ext[1:]
    
    # Case-insensitive matching
    allowed_lower = {e.lower() for e in allowed_extensions}
    return ext.lower() in allowed_lower


def _is_within_destination(full_path, destination):
    """Verify that full_path is within destination directory."""
    # Both paths are already normalized with normcase
    if full_path == destination:
        return True
    
    # Ensure destination ends with separator for proper prefix matching
    if not destination.endswith(os.sep):
        destination += os.sep
    
    return full_path.startswith(destination)
