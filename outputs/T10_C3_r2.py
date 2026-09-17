from copy import deepcopy
from typing import Any, Dict, List


def validate_patch(document: Any, operations: List[Dict], protected_paths: List[str]) -> Dict:
    """
    Validate JSON patch operations against allowed operations, valid paths,
    existing document structure, and protected paths.
    """
    errors = []
    
    try:
        if not isinstance(operations, list):
            return {"valid": False, "errors": ["operations must be a list"]}
        if not isinstance(protected_paths, list):
            return {"valid": False, "errors": ["protected_paths must be a list"]}
    except:
        return {"valid": False, "errors": ["invalid input types"]}
    
    current_doc = deepcopy(document)
    
    def parse_pointer(pointer: str) -> Any:
        """Parse a JSON Pointer (RFC 6901) into tokens."""
        if not isinstance(pointer, str):
            return None
        if pointer == "":
            return []
        if not pointer.startswith("/"):
            return None
        
        tokens = pointer[1:].split("/")
        unescaped = []
        for token in tokens:
            token = token.replace("~1", "/").replace("~0", "~")
            unescaped.append(token)
        return unescaped
    
    def is_path_protected(path: str) -> bool:
        """Check if a path is protected, descendant of protected, or parent of protected."""
        for protected in protected_paths:
            if path == protected or path.startswith(protected + "/"):
                return True
            if protected.startswith(path + "/"):
                return True
        return False
    
    def get_parent_and_token(doc: Any, tokens: List[str]) -> tuple:
        """Navigate to parent of path. Returns (success, parent, last_token)."""
        if not tokens:
            return True, None, None
        
        current = doc
        for token in tokens[:-1]:
            if isinstance(current, dict):
                if token not in current:
                    return False, None, None
                current = current[token]
            elif isinstance(current, list):
                try:
                    idx = int(token)
                    if idx < 0 or idx >= len(current):
                        return False, None, None
                    current = current[idx]
                except (ValueError, TypeError):
                    return False, None, None
            else:
                return False, None, None
        
        return True, current, tokens[-1]
    
    def path_exists(doc: Any, tokens: List[str]) -> bool:
        """Check if a path exists in the document."""
        if not tokens:
            return True
        
        success, parent, last_token = get_parent_and_token(doc, tokens)
        if not success or parent is None:
            return False
        
        if isinstance(parent, dict):
            return last_token in parent
        elif isinstance(parent, list):
            try:
                idx = int(last_token)
                return 0 <= idx < len(parent)
            except (ValueError, TypeError):
                return False
        return False
    
    for i, op in enumerate(operations):
        try:
            if not isinstance(op, dict):
                return {"valid": False, "errors": [f"Operation {i}: not a dict"]}
            
            op_type = op.get("op")
            if op_type not in ("add", "remove", "replace"):
                return {"valid": False, "errors": [f"Operation {i}: invalid op '{op_type}'"]}
            
            path = op.get("path")
            if not isinstance(path, str):
                return {"valid": False, "errors": [f"Operation {i}: path must be a string"]}
            
            tokens = parse_pointer(path)
            if tokens is None:
                return {"valid": False, "errors": [f"Operation {i}: invalid JSON Pointer '{path}'"]}
            
            if is_path_protected(path):
                return {"valid": False, "errors": [f"Operation {i}: path '{path}' is protected"]}
            
            if op_type == "add":
                if "value" not in op:
                    return {"valid": False, "errors": [f"Operation {i}: 'add' requires 'value'"]}
                
                if tokens:
                    success, parent, last_token = get_parent_and_token(current_doc, tokens)
                    if not success or parent is None:
                        return {"valid": False, "errors": [f"Operation {i}: parent does not exist"]}
                    
                    if not isinstance(parent, (dict, list)):
                        return {"valid": False, "errors": [f"Operation {i}: parent is not dict/list"]}
                    
                    if isinstance(parent, list):
                        if last_token == "-":
                            parent.append(deepcopy(op["value"]))
                        else:
                            try:
                                idx = int(last_token)
                                if idx < 0 or idx > len(parent):
                                    return {"valid": False, "errors": [f"Operation {i}: invalid array index"]}
                                parent.insert(idx, deepcopy(op["value"]))
                            except (ValueError, TypeError):
                                return {"valid": False, "errors": [f"Operation {i}: invalid array index"]}
                    else:
                        parent[last_token] = deepcopy(op["value"])
                else:
                    current_doc = deepcopy(op["value"])
            
            elif op_type == "remove":
                if not path_exists(current_doc, tokens):
                    return {"valid": False, "errors": [f"Operation {i}: path does not exist"]}
                
                if not tokens:
                    return {"valid": False, "errors": [f"Operation {i}: cannot remove root"]}
                
                success, parent, last_token = get_parent_and_token(current_doc, tokens)
                if isinstance(parent, dict):
                    del parent[last_token]
                elif isinstance(parent, list):
                    try:
                        idx = int(last_token)
                        del parent[idx]
                    except (ValueError, TypeError):
                        return {"valid": False, "errors": [f"Operation {i}: invalid array index"]}
            
            elif op_type == "replace":
                if "value" not in op:
                    return {"valid": False, "errors": [f"Operation {i}: 'replace' requires 'value'"]}
                
                if not path_exists(current_doc, tokens):
                    return {"valid": False, "errors": [f"Operation {i}: path does not exist"]}
                
                if tokens:
                    success, parent, last_token = get_parent_and_token(current_doc, tokens)
                    if isinstance(parent, dict):
                        parent[last_token] = deepcopy(op["value"])
                    elif isinstance(parent, list):
                        try:
                            idx = int(last_token)
                            parent[idx] = deepcopy(op["value"])
                        except (ValueError, TypeError):
                            return {"valid": False, "errors": [f"Operation {i}: invalid array index"]}
                else:
                    current_doc = deepcopy(op["value"])
        
        except Exception:
            return {"valid": False, "errors": [f"Operation {i}: validation error"]}
    
    return {"valid": True, "errors": []}
