def validate_upload(filename, size_bytes, content_type, config) -> dict:
    errors = []
    
    if not isinstance(config, dict):
        return {"valid": False, "errors": []}
    
    allowed_types = config.get("allowed_types", {})
    max_size_bytes = config.get("max_size_bytes", 0)
    allow_empty_files = config.get("allow_empty_files", False)
    
    filename_valid = False
    if isinstance(filename, str) and filename:
        if ".." not in filename and "/" not in filename and "\\" not in filename and "\0" not in filename:
            filename_valid = True
    
    if not filename_valid:
        errors.append("filename")
    
    extension = None
    if filename_valid and "." in filename:
        extension = filename.rsplit(".", 1)[-1].lower()
    
    if extension is None or extension not in allowed_types:
        errors.append("extension")
    elif not isinstance(content_type, str) or content_type != allowed_types[extension]:
        errors.append("content_type")
    
    if not isinstance(size_bytes, int) or size_bytes < 0:
        errors.append("size")
    else:
        if (not allow_empty_files and size_bytes == 0) or size_bytes > max_size_bytes:
            errors.append("size")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
