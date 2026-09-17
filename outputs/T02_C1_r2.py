def validate_upload(filename, size_bytes, content_type, config) -> dict:
    errors = []
    
    if not isinstance(config, dict):
        config = {}
    
    filename_valid = False
    if filename and isinstance(filename, str) and filename.strip():
        filename = filename.strip()
        filename_valid = True
    else:
        errors.append("filename")
    
    if filename_valid:
        if '.' in filename:
            ext = filename.rsplit('.', 1)[-1].lower()
            allowed_types = config.get("allowed_types", {})
            if ext not in allowed_types:
                errors.append("extension")
            else:
                if content_type != allowed_types[ext]:
                    errors.append("content_type")
        else:
            errors.append("extension")
    
    try:
        size_int = int(size_bytes)
        allow_empty = config.get("allow_empty_files", False)
        max_size = config.get("max_size_bytes", 0)
        
        if not allow_empty and size_int == 0:
            errors.append("size")
        elif size_int > max_size:
            errors.append("size")
    except (TypeError, ValueError):
        errors.append("size")
    
    return {"valid": len(errors) == 0, "errors": errors}
