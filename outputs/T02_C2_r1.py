def validate_upload(filename, size_bytes, content_type, config) -> dict:
    errors = []
    
    # Validate config is dict
    if not isinstance(config, dict):
        return {"valid": False, "errors": ["filename"]}
    
    # Validate filename
    if not isinstance(filename, str) or not filename:
        errors.append("filename")
    elif "/" in filename or "\\" in filename or ".." in filename or "\0" in filename:
        errors.append("filename")
    
    # Validate extension
    extension = None
    if "filename" not in errors:
        if "." not in filename:
            errors.append("extension")
        else:
            ext = filename.rsplit(".", 1)[-1].lower()
            allowed_types = config.get("allowed_types", {})
            
            if not ext or ext not in allowed_types:
                errors.append("extension")
            else:
                extension = ext
    
    # Validate content type
    if extension:
        allowed_types = config.get("allowed_types", {})
        if content_type != allowed_types[extension]:
            errors.append("content_type")
    
    # Validate size
    if not isinstance(size_bytes, (int, float)) or size_bytes < 0:
        errors.append("size")
    else:
        if size_bytes == 0 and not config.get("allow_empty_files", False):
            errors.append("size")
        
        max_size = config.get("max_size_bytes")
        if max_size is not None and size_bytes > max_size:
            errors.append("size")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
