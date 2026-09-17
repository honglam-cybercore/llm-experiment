def validate_upload(filename, size_bytes, content_type, config) -> dict:
    errors = []
    
    try:
        # Ensure config is a dict
        if not isinstance(config, dict):
            config = {}
        
        # 1. Validate filename
        if not isinstance(filename, str) or not filename:
            errors.append("filename")
        elif "/" in filename or "\\" in filename or ".." in filename or "\x00" in filename:
            errors.append("filename")
        
        # 2. Validate size
        if not isinstance(size_bytes, int) or size_bytes < 0:
            errors.append("size")
        else:
            max_size = config.get("max_size_bytes")
            allow_empty = config.get("allow_empty_files", False)
            
            if size_bytes == 0 and not allow_empty:
                errors.append("size")
            elif max_size is not None and size_bytes > max_size:
                errors.append("size")
        
        # 3 & 4. Validate extension and content_type
        if "filename" not in errors and isinstance(filename, str):
            if "." not in filename:
                errors.append("extension")
            else:
                ext = filename.rsplit(".", 1)[-1].lower()
                allowed_types = config.get("allowed_types", {})
                
                if ext not in allowed_types:
                    errors.append("extension")
                elif not isinstance(content_type, str) or content_type != allowed_types[ext]:
                    errors.append("content_type")
    
    except:
        return {"valid": False, "errors": ["filename"]}
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
