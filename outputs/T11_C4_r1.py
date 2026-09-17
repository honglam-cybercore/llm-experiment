def validate_entries(entries, destination, config) -> dict:
    import os
    
    result = {
        "valid": True,
        "errors": [],
        "rejected": []
    }
    
    # Validate inputs
    try:
        if not isinstance(entries, list):
            raise TypeError("entries must be a list")
        if not isinstance(destination, str):
            raise TypeError("destination must be a string")
        if not isinstance(config, dict):
            raise TypeError("config must be a dict")
        if "allowed_extensions" not in config:
            raise ValueError("config must contain 'allowed_extensions'")
        if not isinstance(config["allowed_extensions"], list):
            raise TypeError("allowed_extensions must be a list")
    except Exception as e:
        result["valid"] = False
        result["errors"].append(str(e))
        return result
    
    # Normalize destination path
    try:
        dest_normalized = os.path.normpath(destination)
        dest_absolute = os.path.abspath(dest_normalized)
    except Exception as e:
        result["valid"] = False
        result["errors"].append(f"Invalid destination: {str(e)}")
        return result
    
    seen_normalized = {}
    allowed_extensions = set(ext.lower().lstrip('.') for ext in config["allowed_extensions"])
    
    for entry in entries:
        if not isinstance(entry, str):
            result["valid"] = False
            result["errors"].append(f"Entry must be string, got {type(entry).__name__}")
            result["rejected"].append(str(entry))
            continue
        
        if not entry:
            result["valid"] = False
            result["errors"].append("Empty entry")
            result["rejected"].append(entry)
            continue
        
        # Check for absolute POSIX path
        if entry.startswith('/'):
            result["valid"] = False
            result["errors"].append(f"{entry}: Absolute POSIX path")
            result["rejected"].append(entry)
            continue
        
        # Check for Windows drive letter
        if len(entry) >= 2 and entry[1] == ':' and entry[0].isalpha():
            result["valid"] = False
            result["errors"].append(f"{entry}: Windows drive path")
            result["rejected"].append(entry)
            continue
        
        # Check for UNC path
        if entry.startswith('\\\\'):
            result["valid"] = False
            result["errors"].append(f"{entry}: UNC path")
            result["rejected"].append(entry)
            continue
        
        # Check for mixed separators
        if '/' in entry and '\\' in entry:
            result["valid"] = False
            result["errors"].append(f"{entry}: Mixed separators")
            result["rejected"].append(entry)
            continue
        
        # Normalize and check for parent directory traversal
        normalized_entry = entry.replace('\\', '/')
        parts = [p for p in normalized_entry.split('/') if p]
        
        # Check for reserved Windows device names
        reserved_names = {'con', 'prn', 'aux', 'nul', 'com1', 'com2', 'com3', 'com4',
                         'com5', 'com6', 'com7', 'com8', 'com9', 'lpt1', 'lpt2', 'lpt3',
                         'lpt4', 'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9'}
        if parts and parts[0].lower() in reserved_names:
            result["valid"] = False
            result["errors"].append(f"{entry}: Reserved device name")
            result["rejected"].append(entry)
            continue
        
        # Check for parent directory traversal
        if '..' in parts:
            result["valid"] = False
            result["errors"].append(f"{entry}: Parent directory traversal")
            result["rejected"].append(entry)
            continue
        
        try:
            # Normalize and join paths
            entry_normalized = entry.replace('\\', '/')
            full_path = os.path.normpath(os.path.join(dest_absolute, entry_normalized))
            
            # Verify path stays within destination
            rel_path = os.path.relpath(full_path, dest_absolute)
            if rel_path.startswith('..') or rel_path == '.':
                result["valid"] = False
                result["errors"].append(f"{entry}: Path escapes destination")
                result["rejected"].append(entry)
                continue
        except ValueError:
            # Different drives on Windows
            result["valid"] = False
            result["errors"].append(f"{entry}: Path on different drive")
            result["rejected"].append(entry)
            continue
        except Exception as e:
            result["valid"] = False
            result["errors"].append(f"{entry}: Error processing path")
            result["rejected"].append(entry)
            continue
        
        # Check file extension
        _, ext = os.path.splitext(entry)
        ext_clean = ext.lstrip('.').lower() if ext else ''
        if ext_clean not in allowed_extensions:
            result["valid"] = False
            result["errors"].append(f"{entry}: Extension not allowed")
            result["rejected"].append(entry)
            continue
        
        # Check for duplicate normalized paths
        if full_path in seen_normalized:
            result["valid"] = False
            result["errors"].append(f"{entry}: Duplicate destination")
            result["rejected"].append(entry)
            continue
        
        seen_normalized[full_path] = entry
    
    return result
