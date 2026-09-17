def validate_upload(filename, size_bytes, content_type, config) -> dict:
    errors = []
    extension = None
    
    # Check filename
    if not isinstance(filename, str) or not filename.strip():
        errors.append("filename")
    else:
        # Extract extension from filename
        parts = filename.rsplit('.', 1)
        if len(parts) == 2 and parts[1].strip():
            extension = parts[1].lower().strip()
    
    # Check extension
    allowed_types = config.get("allowed_types", {}) if isinstance(config, dict) else {}
    if extension is None or extension not in allowed_types:
        errors.append("extension")
    else:
        # Check content_type (only if extension is valid)
        allowed_content_type = allowed_types[extension]
        if content_type != allowed_content_type:
            errors.append("content_type")
    
    # Check size
    try:
        size_int = int(size_bytes)
        max_size = config.get("max_size_bytes") if isinstance(config, dict) else None
        allow_empty = config.get("allow_empty_files", False) if isinstance(config, dict) else False
        
        if size_int < 0:
            errors.append("size")
        elif size_int == 0 and not allow_empty:
            errors.append("size")
        elif max_size is not None and size_int > max_size:
            errors.append("size")
    except (TypeError, ValueError):
        errors.append("size")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
