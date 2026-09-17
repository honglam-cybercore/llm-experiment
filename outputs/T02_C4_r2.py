def validate_upload(filename, size_bytes, content_type, config) -> dict:
    errors = []
    
    try:
        if not isinstance(config, dict):
            return {"valid": False, "errors": ["filename", "extension", "content_type", "size"]}
        
        if not _is_valid_filename(filename):
            errors.append("filename")
        
        extension = _extract_extension(filename)
        allowed_types = config.get('allowed_types', {})
        
        if extension not in allowed_types:
            errors.append("extension")
        elif content_type != allowed_types[extension]:
            errors.append("content_type")
        
        if not _is_valid_size(size_bytes, config):
            errors.append("size")
    
    except Exception:
        return {"valid": False, "errors": ["filename", "extension", "content_type", "size"]}
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


def _is_valid_filename(filename):
    if not isinstance(filename, str) or len(filename) == 0:
        return False
    if '\0' in filename or '/' in filename or '\\' in filename or '..' in filename:
        return False
    return True


def _extract_extension(filename):
    if not isinstance(filename, str) or '.' not in filename:
        return None
    parts = filename.rsplit('.', 1)
    if len(parts) != 2 or not parts[1]:
        return None
    return parts[1].lower()


def _is_valid_size(size_bytes, config):
    if not isinstance(size_bytes, int) or isinstance(size_bytes, bool):
        return False
    if size_bytes < 0:
        return False
    if size_bytes == 0 and not config.get('allow_empty_files', False):
        return False
    if size_bytes > config.get('max_size_bytes', 0):
        return False
    return True
