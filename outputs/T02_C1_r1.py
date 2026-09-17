def validate_upload(filename, size_bytes, content_type, config) -> dict:
    errors = []
    
    try:
        if not isinstance(config, dict):
            return {"valid": False, "errors": ["filename"]}
        
        if not isinstance(filename, str) or not filename or filename.isspace():
            errors.append("filename")
        
        if filename and isinstance(filename, str) and not filename.isspace():
            if '.' not in filename:
                errors.append("extension")
            else:
                ext = filename.rsplit('.', 1)[-1].lower()
                allowed_types = config.get("allowed_types", {})
                
                if ext not in allowed_types:
                    errors.append("extension")
                else:
                    if not isinstance(content_type, str):
                        errors.append("content_type")
                    else:
                        allowed_content_type = allowed_types[ext]
                        if content_type != allowed_content_type:
                            errors.append("content_type")
        
        if isinstance(size_bytes, bool) or not isinstance(size_bytes, int):
            errors.append("size")
        else:
            max_size = config.get("max_size_bytes", 0)
            allow_empty = config.get("allow_empty_files", False)
            
            if size_bytes < 0 or size_bytes > max_size:
                errors.append("size")
            elif size_bytes == 0 and not allow_empty:
                errors.append("size")
    
    except Exception:
        return {"valid": False, "errors": ["filename"]}
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
