import os
from pathlib import Path


def validate_entries(entries, destination, config) -> dict:
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
        
        if not isinstance(config, dict):
            result["errors"].append("config must be a dict")
            return result
        
        if "allowed_extensions" not in config:
            result["errors"].append("config must contain allowed_extensions")
            return result
        
        allowed_extensions = config["allowed_extensions"]
        if not isinstance(allowed_extensions, list):
            result["errors"].append("allowed_extensions must be a list")
            return result
        
        allowed_extensions_lower = [ext.lower() for ext in allowed_extensions]
    except:
        result["errors"].append("Invalid input parameters")
        return result
    
    try:
        dest_path = os.path.normpath(os.path.abspath(destination))
    except:
        result["errors"].append("Invalid destination path")
        return result
    
    reserved_names = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    
    rejected_entries = set()
    seen_normalized_paths = {}
    
    for entry in entries:
        try:
            if not isinstance(entry, str):
                result["errors"].append("Entry must be a string")
                result["rejected"].append(entry)
                rejected_entries.add(entry)
                continue
            
            if os.path.isabs(entry) or entry.startswith('/') or entry.startswith('\\'):
                result["errors"].append(f"Absolute path rejected: {entry}")
                result["rejected"].append(entry)
                rejected_entries.add(entry)
                continue
            
            if entry.startswith('\\\\') or entry.startswith('//'):
                result["errors"].append(f"UNC path rejected: {entry}")
                result["rejected"].append(entry)
                rejected_entries.add(entry)
                continue
            
            if len(entry) >= 2 and entry[1] == ':':
                result["errors"].append(f"Drive letter rejected: {entry}")
                result["rejected"].append(entry)
                rejected_entries.add(entry)
                continue
            
            if '..' in entry:
                result["errors"].append(f"Directory traversal rejected: {entry}")
                result["rejected"].append(entry)
                rejected_entries.add(entry)
                continue
            
            path_parts = entry.replace('\\', '/').split('/')
            found_reserved = False
            for part in path_parts:
                if part:
                    base_name = part.split('.')[0].upper()
                    if base_name in reserved_names:
                        result["errors"].append(f"Reserved device name rejected: {entry}")
                        result["rejected"].append(entry)
                        rejected_entries.add(entry)
                        found_reserved = True
                        break
            
            if found_reserved:
                continue
            
            _, file_ext = os.path.splitext(entry)
            ext_clean = file_ext.lstrip('.').lower() if file_ext else ''
            
            if ext_clean not in allowed_extensions_lower:
                result["errors"].append(f"Extension not allowed: {entry}")
                result["rejected"].append(entry)
                rejected_entries.add(entry)
                continue
            
            normalized_full_path = os.path.normpath(os.path.join(dest_path, entry))
            
            try:
                Path(normalized_full_path).relative_to(dest_path)
            except ValueError:
                result["errors"].append(f"Path escapes destination: {entry}")
                result["rejected"].append(entry)
                rejected_entries.add(entry)
                continue
            
            if normalized_full_path in seen_normalized_paths:
                seen_normalized_paths[normalized_full_path].append(entry)
            else:
                seen_normalized_paths[normalized_full_path] = [entry]
        
        except Exception:
            result["errors"].append(f"Validation error processing entry")
            result["rejected"].append(entry)
            rejected_entries.add(entry)
    
    for norm_path, entries_list in seen_normalized_paths.items():
        if len(entries_list) > 1:
            for ent in entries_list:
                if ent not in rejected_entries:
                    result["rejected"].append(ent)
                    result["errors"].append(f"Duplicate normalized destination: {ent}")
                    rejected_entries.add(ent)
    
    result["valid"] = len(rejected_entries) == 0
    
    return result
