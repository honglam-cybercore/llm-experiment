def validate_upload(filename, size_bytes, content_type, config) -> dict:
    errors = set()
    
    try:
        if not isinstance(config, dict):
            return {"valid": False, "errors": ["filename", "extension", "content_type", "size"]}
        
        if "allowed_types" not in config or "max_size_bytes" not in config or "allow_empty_files" not in config:
            return {"valid": False, "errors": ["filename", "extension", "content_type", "size"]}
        
        allowed_types = config["allowed_types"]
        max_size_bytes = config["max_size_bytes"]
        allow_empty_files = config["allow_empty_files"]
        
        if not isinstance(allowed_types, dict) or not isinstance(max_size_bytes, int) or not isinstance(allow_empty_files, bool):
            return {"valid": False, "errors": ["filename", "extension", "content_type", "size"]}
        
        if not isinstance(filename, str) or not filename:
            errors.add("filename")
        elif ".." in filename or "/" in filename or "\\" in filename:
            errors.add("filename")
        
        if not isinstance(size_bytes, int):
            errors.add("size")
        elif size_bytes < 0:
            errors.add("size")
        elif size_bytes == 0 and not allow_empty_files:
            errors.add("size")
        elif size_bytes > max_size_bytes:
            errors.add("size")
        
        content_type_valid = isinstance(content_type, str) and content_type
        if not content_type_valid:
            errors.add("content_type")
        
        extension = None
        if isinstance(filename, str) and filename and "." in filename:
            extension = filename.rsplit(".", 1)[-1].lower()
        
        if not extension or extension not in allowed_types:
            errors.add("extension")
        elif content_type_valid and content_type != allowed_types[extension]:
            errors.add("content_type")
    
    except Exception:
        return {"valid": False, "errors": ["filename", "extension", "content_type", "size"]}
    
    return {
        "valid": len(errors) == 0,
        "errors": list(errors)
    }
