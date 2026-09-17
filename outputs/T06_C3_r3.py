def evaluate_access(user, resource, action, policy) -> dict:
    if not isinstance(user, dict) or not isinstance(resource, dict) or not isinstance(policy, dict):
        return {"allowed": False, "reasons": ["Invalid input structure"]}
    
    if not isinstance(action, str):
        return {"allowed": False, "reasons": ["Invalid action"]}
    
    if user.get("status") != "active":
        return {"allowed": False, "reasons": ["User account is inactive"]}
    
    actions = policy.get("actions")
    if not isinstance(actions, list) or action not in actions:
        return {"allowed": False, "reasons": ["Action is not defined in policy"]}
    
    user_role = user.get("role")
    valid_roles = {"user", "manager", "administrator"}
    if user_role not in valid_roles:
        return {"allowed": False, "reasons": ["Unknown role"]}
    
    classification = resource.get("classification")
    valid_classifications = {"normal", "confidential"}
    if classification not in valid_classifications:
        return {"allowed": False, "reasons": ["Unknown classification"]}
    
    required_permissions = policy.get("required_permissions", {})
    if classification in required_permissions:
        required_perm = required_permissions[classification]
        user_permissions = user.get("permissions", [])
        if required_perm not in user_permissions:
            return {"allowed": False, "reasons": ["Missing required permission"]}
    
    rules = policy.get("rules", [])
    if not isinstance(rules, list):
        rules = []
    
    for rule in rules:
        if not isinstance(rule, dict) or rule.get("effect") != "deny":
            continue
        matches = True
        if "role" in rule and rule["role"] != user_role:
            matches = False
        if "action" in rule and rule["action"] != action:
            matches = False
        if "classification" in rule and rule["classification"] != classification:
            matches = False
        if matches:
            return {"allowed": False, "reasons": ["Denied by policy rule"]}
    
    for rule in rules:
        if not isinstance(rule, dict) or rule.get("effect") != "allow":
            continue
        matches = True
        if "role" in rule and rule["role"] != user_role:
            matches = False
        if "action" in rule and rule["action"] != action:
            matches = False
        if "classification" in rule and rule["classification"] != classification:
            matches = False
        if matches:
            return {"allowed": True, "reasons": ["Allowed by policy rule"]}
    
    if user_role == "administrator":
        return {"allowed": True, "reasons": ["Administrator can perform any action"]}
    elif user_role == "manager":
        user_department = user.get("department")
        resource_department = resource.get("department")
        if user_department is not None and user_department == resource_department:
            return {"allowed": True, "reasons": ["Manager can perform action on resources in their department"]}
        else:
            return {"allowed": False, "reasons": ["Manager cannot perform action on this resource"]}
    else:
        user_id = user.get("id")
        owner_id = resource.get("owner_id")
        if user_id is not None and user_id == owner_id:
            return {"allowed": True, "reasons": ["User can perform action on owned resources"]}
        else:
            return {"allowed": False, "reasons": ["User cannot perform action on this resource"]}
