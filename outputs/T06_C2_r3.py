def evaluate_access(user, resource, action, policy) -> dict:
    if not isinstance(user, dict):
        return {"allowed": False, "reasons": ["Invalid user"]}
    if not isinstance(resource, dict):
        return {"allowed": False, "reasons": ["Invalid resource"]}
    if not isinstance(policy, dict):
        return {"allowed": False, "reasons": ["Invalid policy"]}
    if not isinstance(action, str):
        return {"allowed": False, "reasons": ["Invalid action"]}
    
    if user.get("status") != "active":
        return {"allowed": False, "reasons": ["User is not active"]}
    
    if user.get("role") not in ("user", "manager", "administrator"):
        return {"allowed": False, "reasons": ["Unknown role"]}
    
    permissions = user.get("permissions", [])
    if not isinstance(permissions, list):
        return {"allowed": False, "reasons": ["Invalid permissions"]}
    
    if resource.get("classification") not in ("normal", "confidential"):
        return {"allowed": False, "reasons": ["Unknown classification"]}
    
    actions = policy.get("actions", [])
    if not isinstance(actions, list) or action not in actions:
        return {"allowed": False, "reasons": ["Action not defined in policy"]}
    
    required_perms = policy.get("required_permissions", {})
    if not isinstance(required_perms, dict):
        return {"allowed": False, "reasons": ["Invalid required_permissions"]}
    
    required_permission = required_perms.get(resource.get("classification"))
    if required_permission and required_permission not in permissions:
        return {"allowed": False, "reasons": ["Missing required permission"]}
    
    rules = policy.get("rules", [])
    if not isinstance(rules, list):
        return {"allowed": False, "reasons": ["Invalid rules"]}
    
    for rule in rules:
        if isinstance(rule, dict) and rule.get("effect") == "deny":
            if _rule_matches(rule, user, resource, action):
                return {"allowed": False, "reasons": ["Denied by policy rule"]}
    
    for rule in rules:
        if isinstance(rule, dict) and rule.get("effect") == "allow":
            if _rule_matches(rule, user, resource, action):
                return {"allowed": True, "reasons": ["Allowed by policy rule"]}
    
    role = user.get("role")
    
    if role == "administrator":
        return {"allowed": True, "reasons": ["Administrator access"]}
    
    if role == "manager" and user.get("department") == resource.get("department"):
        return {"allowed": True, "reasons": ["Manager access to own department"]}
    
    if role == "user" and user.get("id") == resource.get("owner_id"):
        return {"allowed": True, "reasons": ["User owns resource"]}
    
    return {"allowed": False, "reasons": ["Access denied"]}


def _rule_matches(rule, user, resource, action):
    if "role" in rule and rule["role"] != user.get("role"):
        return False
    if "action" in rule and rule["action"] != action:
        return False
    if "classification" in rule and rule["classification"] != resource.get("classification"):
        return False
    return True
