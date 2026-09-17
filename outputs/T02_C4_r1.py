def validate_upload(filename, size_bytes, content_type, config) -> dict:
    errors = []
    
    try:
        # Validate config structure
        if not isinstance(config, dict):
            return {"valid": False, "errors": []}
        
        allowed_types = config.get("allowed_types", {})
        max_size_bytes = config.get("max_size_bytes")
        allow_empty_files = config.get("allow_empty_files", False)
        
        if not isinstance(allowed_types, dict) or not isinstance(max_size_bytes, int) or not isinstance(allow_empty_files, bool) or max_size_bytes < 0:
            return {"valid": False, "errors": []}
        
        # Validate filename
        if not isinstance(filename, str) or not filename:
            errors.append("filename")
        elif "\x00" in filename or "/" in filename or "\\" in filename or ".." in filename:
            errors.append("filename")
        elif filename.startswith("."):
            errors.append("filename")
        
        # Extract and validate extension
        if "filename" not in errors:
            if "." not in filename:
                errors.append("extension")
            else:
                ext = filename.rsplit(".", 1)[-1].lower()
                
                if ext not in allowed_types:
                    errors.append("extension")
                else:
                    # Validate content type matches extension
                    if not isinstance(content_type, str) or content_type != allowed_types[ext]:
                        errors.append("content_type")
        
        # Validate file size
        if not isinstance(size_bytes, int) or size_bytes < 0:
            errors.append("size")
        elif size_bytes == 0 and not allow_empty_files:
            errors.append("size")
        elif size_bytes > max_size_bytes:
            errors.append("size")
        
        return {"valid": len(errors) == 0, "errors": errors}
    
    except Exception:
        return {"valid": False, "errors": []}
