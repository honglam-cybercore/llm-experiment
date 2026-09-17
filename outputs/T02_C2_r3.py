def validate_upload(filename, size_bytes, content_type, config) -> dict:
    errors = []
    
    try:
        if not isinstance(config, dict):
            return {"valid": False, "errors": ["filename"]}
        
        if not isinstance(filename, str):
            errors.append("filename")
        elif not filename:
            errors.append("filename")
        elif '/' in filename or '\\' in filename:
            errors.append("filename")
        elif '..' in filename or filename.startswith('.'):
            errors.append("filename")
        else:
            if '.' not in filename:
                errors.append("extension")
            else:
                extension = filename.rsplit('.', 1)[-1].lower()
                allowed_types = config.get("allowed_types", {})
                
                if extension not in allowed_types:
                    errors.append("extension")
                else:
                    if not isinstance(content_type, str) or content_type != allowed_types[extension]:
                        errors.append("content_type")
        
        if not isinstance(size_bytes, int):
            errors.append("size")
        elif size_bytes < 0:
            errors.append("size")
        elif size_bytes == 0 and not config.get("allow_empty_files", False):
            errors.append("size")
        elif size_bytes > config.get("max_size_bytes", 0):
            errors.append("size")
    
    except Exception:
        return {"valid": False, "errors": ["filename"]}
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
