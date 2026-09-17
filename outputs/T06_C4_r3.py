def evaluate_access(user, resource, action, policy) -> dict:
    try:
        if not isinstance(user, dict) or not isinstance(resource, dict) or not isinstance(policy, dict):
            return {"allowed": False, "reasons": ["Invalid input structure"]}
        
        if user.get("status") == "inactive":
            return {"allowed": False, "reasons": ["User account is inactive"]}
        
        policy_actions = policy.get("actions")
        if not isinstance(policy_actions, list) or action not in policy_actions:
            return {"allowed": False, "reasons": ["Action is not defined in policy"]}
        
        user_role = user.get("role")
        valid_roles = {"user", "manager", "administrator"}
        if user_role not in valid_roles:
            return {"allowed": False, "reasons": ["Invalid user role"]}
        
        classification = resource.get("classification")
        valid_classifications = {"normal", "confidential"}
        if classification not in valid_classifications:
            return {"allowed": False, "reasons": ["Invalid resource classification"]}
        
        required_permissions = policy.get("required_permissions")
        if isinstance(required_permissions, dict) and classification in required_permissions:
            required_perm = required_permissions[classification]
            user_permissions = user.get("permissions")
            if not isinstance(user_permissions, list) or required_perm not in user_permissions:
                return {"allowed": False, "reasons": ["Required permission not held"]}
        
        rules = policy.get("rules")
        if isinstance(rules, list):
            for rule in rules:
                if isinstance(rule, dict) and rule.get("effect") == "deny":
                    if _rule_matches(rule, user_role, action, classification):
                        return {"allowed": False, "reasons": ["Denied by policy rule"]}
        
        if isinstance(rules, list):
            for rule in rules:
                if isinstance(rule, dict) and rule.get("effect") == "allow":
                    if _rule_matches(rule, user_role, action, classification):
                        return {"allowed": True, "reasons": ["Allowed by policy rule"]}
        
        if user_role == "administrator":
            return {"allowed": True, "reasons": ["Administrator can access any resource"]}
        
        if user_role == "manager":
            user_department = user.get("department")
            resource_department = resource.get("department")
            if user_department is not None and resource_department is not None and user_department == resource_department:
                return {"allowed": True, "reasons": ["Manager can access resources in their department"]}
        
        if user_role == "user":
            user_id = user.get("id")
            owner_id = resource.get("owner_id")
            if user_id is not None and owner_id is not None and user_id == owner_id:
                return {"allowed": True, "reasons": ["User can access owned resources"]}
        
        return {"allowed": False, "reasons": ["Access denied"]}
    
    except Exception:
        return {"allowed": False, "reasons": ["Error evaluating access"]}


def _rule_matches(rule, user_role, action, classification):
    if "role" in rule and rule.get("role") != user_role:
        return False
    if "action" in rule and rule.get("action") != action:
        return False
    if "classification" in rule and rule.get("classification") != classification:
        return False
    return True
