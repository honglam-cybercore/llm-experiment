def evaluate_access(user, resource, action, policy) -> dict:
    if user is None or resource is None or action is None or policy is None:
        return {"allowed": False, "reasons": ["Missing required input"]}
    
    if not isinstance(user, dict) or not isinstance(resource, dict) or not isinstance(action, str) or not isinstance(policy, dict):
        return {"allowed": False, "reasons": ["Invalid input types"]}
    
    try:
        if user.get("status") != "active":
            return {"allowed": False, "reasons": ["User account is inactive"]}
        
        policy_actions = policy.get("actions")
        if not isinstance(policy_actions, list) or action not in policy_actions:
            return {"allowed": False, "reasons": ["Action not defined in policy"]}
        
        valid_roles = {"user", "manager", "administrator"}
        user_role = user.get("role")
        if user_role not in valid_roles:
            return {"allowed": False, "reasons": ["Invalid user role"]}
        
        valid_classifications = {"normal", "confidential"}
        resource_classification = resource.get("classification")
        if resource_classification not in valid_classifications:
            return {"allowed": False, "reasons": ["Invalid resource classification"]}
        
        required_permissions = policy.get("required_permissions")
        if isinstance(required_permissions, dict) and resource_classification in required_permissions:
            required_perm = required_permissions[resource_classification]
            user_permissions = user.get("permissions", [])
            if not isinstance(user_permissions, list) or required_perm not in user_permissions:
                return {"allowed": False, "reasons": ["Missing required permission"]}
        
        rules = policy.get("rules", [])
        if isinstance(rules, list):
            for rule in rules:
                if isinstance(rule, dict) and rule.get("effect") == "deny":
                    if _matches_rule(user, resource, action, rule):
                        return {"allowed": False, "reasons": ["Denied by policy rule"]}
        
        if isinstance(rules, list):
            for rule in rules:
                if isinstance(rule, dict) and rule.get("effect") == "allow":
                    if _matches_rule(user, resource, action, rule):
                        return {"allowed": True, "reasons": ["Allowed by policy rule"]}
        
        if user_role == "administrator":
            return {"allowed": True, "reasons": ["Allowed: administrator"]}
        elif user_role == "manager":
            if user.get("department") == resource.get("department"):
                return {"allowed": True, "reasons": ["Allowed: manager in same department"]}
            else:
                return {"allowed": False, "reasons": ["Denied: manager outside department"]}
        else:
            if user.get("id") == resource.get("owner_id"):
                return {"allowed": True, "reasons": ["Allowed: user owns resource"]}
            else:
                return {"allowed": False, "reasons": ["Denied: user does not own resource"]}
    
    except Exception:
        return {"allowed": False, "reasons": ["Error evaluating access"]}


def _matches_rule(user, resource, action, rule):
    if "role" in rule and user.get("role") != rule["role"]:
        return False
    if "action" in rule and action != rule["action"]:
        return False
    if "classification" in rule and resource.get("classification") != rule["classification"]:
        return False
    return True
