def validate_upload(filename, size_bytes, content_type, config) -> dict:
    errors = []
    
    # Validate filename
    if not isinstance(filename, str) or not filename or "\0" in filename:
        errors.append("filename")
    elif ".." in filename or "/" in filename or "\\" in filename:
        errors.append("filename")
    else:
        # Extract and validate extension
        if "." not in filename:
            errors.append("extension")
        else:
            extension = filename.rsplit(".", 1)[-1].lower()
            
            allowed_types = config.get("allowed_types", {})
            if not extension or extension not in allowed_types:
                errors.append("extension")
            else:
                # Validate content type
                expected_content_type = allowed_types[extension]
                if content_type != expected_content_type:
                    errors.append("content_type")
    
    # Validate size
    if isinstance(size_bytes, bool) or not isinstance(size_bytes, int) or size_bytes < 0:
        errors.append("size")
    else:
        max_size = config.get("max_size_bytes", float('inf'))
        allow_empty = config.get("allow_empty_files", False)
        
        if size_bytes > max_size:
            errors.append("size")
        elif not allow_empty and size_bytes == 0:
            errors.append("size")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
