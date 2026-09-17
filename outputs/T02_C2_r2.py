def validate_upload(filename, size_bytes, content_type, config) -> dict:
    errors = []
    
    # Validate config
    if not isinstance(config, dict):
        return {"valid": False, "errors": ["filename", "extension", "content_type", "size"]}
    
    # Validate filename
    filename_valid = True
    if not isinstance(filename, str) or not filename or filename.isspace():
        errors.append("filename")
        filename_valid = False
    elif filename.startswith("."):
        errors.append("filename")
        filename_valid = False
    elif ".." in filename or "/" in filename or "\\" in filename:
        errors.append("filename")
        filename_valid = False
    
    # Extract extension
    ext = ""
    if filename_valid and "." in filename:
        ext = filename.rsplit(".", 1)[-1].lower()
    
    # Validate extension
    allowed_types = config.get("allowed_types", {})
    if ext not in allowed_types:
        errors.append("extension")
    
    # Validate content type (only if extension is valid)
    if ext in allowed_types:
        allowed_content_type = allowed_types[ext]
        if not isinstance(content_type, str) or content_type != allowed_content_type:
            errors.append("content_type")
    
    # Validate size
    if not isinstance(size_bytes, int) or size_bytes < 0:
        errors.append("size")
    else:
        max_size = config.get("max_size_bytes", 0)
        if size_bytes > max_size:
            errors.append("size")
        
        if size_bytes == 0 and not config.get("allow_empty_files", False):
            errors.append("size")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
