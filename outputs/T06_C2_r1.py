def evaluate_access(user, resource, action, policy) -> dict:
    reasons = []
    
    try:
        # Safe extraction with defaults
        user_status = user.get("status") if isinstance(user, dict) else None
        user_role = user.get("role") if isinstance(user, dict) else None
        user_id = user.get("id") if isinstance(user, dict) else None
        user_department = user.get("department") if isinstance(user, dict) else None
        user_permissions = user.get("permissions", []) if isinstance(user, dict) else []
        
        resource_owner_id = resource.get("owner_id") if isinstance(resource, dict) else None
        resource_department = resource.get("department") if isinstance(resource, dict) else None
        resource_classification = resource.get("classification") if isinstance(resource, dict) else None
        
        policy_actions = policy.get("actions", []) if isinstance(policy, dict) else []
        policy_rules = policy.get("rules", []) if isinstance(policy, dict) else []
        policy_required_permissions = policy.get("required_permissions", {}) if isinstance(policy, dict) else {}
        
        # Ensure lists and dicts
        if not isinstance(user_permissions, list):
            user_permissions = []
        if not isinstance(policy_actions, list):
            policy_actions = []
        if not isinstance(policy_rules, list):
            policy_rules = []
        if not isinstance(policy_required_permissions, dict):
            policy_required_permissions = {}
    except:
        return {"allowed": False, "reasons": ["Invalid input structure"]}
    
    # Pre-checks that deny outright
    if user_status != "active":
        reasons.append("User is not active")
        return {"allowed": False, "reasons": reasons}
    
    if action not in policy_actions:
        reasons.append(f"Action '{action}' is not defined in policy")
        return {"allowed": False, "reasons": reasons}
    
    known_roles = {"user", "manager", "administrator"}
    if user_role not in known_roles:
        reasons.append(f"Unknown role '{user_role}'")
        return {"allowed": False, "reasons": reasons}
    
    known_classifications = {"normal", "confidential"}
    if resource_classification not in known_classifications:
        reasons.append(f"Unknown classification '{resource_classification}'")
        return {"allowed": False, "reasons": reasons}
    
    if resource_classification in policy_required_permissions:
        required_permission = policy_required_permissions[resource_classification]
        if required_permission not in user_permissions:
            reasons.append(f"Missing required permission '{required_permission}'")
            return {"allowed": False, "reasons": reasons}
    
    # Check explicit DENY rules
    for rule in policy_rules:
        if not isinstance(rule, dict):
            continue
        if rule.get("effect") == "deny":
            matches = True
            for key, value in rule.items():
                if key == "effect":
                    continue
                if key == "role" and value != user_role:
                    matches = False
                    break
                elif key == "action" and value != action:
                    matches = False
                    break
                elif key == "classification" and value != resource_classification:
                    matches = False
                    break
            if matches:
                reasons.append("Explicit deny rule matched")
                return {"allowed": False, "reasons": reasons}
    
    # Check explicit ALLOW rules
    for rule in policy_rules:
        if not isinstance(rule, dict):
            continue
        if rule.get("effect") == "allow":
            matches = True
            for key, value in rule.items():
                if key == "effect":
                    continue
                if key == "role" and value != user_role:
                    matches = False
                    break
                elif key == "action" and value != action:
                    matches = False
                    break
                elif key == "classification" and value != resource_classification:
                    matches = False
                    break
            if matches:
                reasons.append("Allow rule matched")
                return {"allowed": True, "reasons": reasons}
    
    # Built-in rules
    if user_role == "administrator":
        reasons.append("Administrator can access any resource")
        return {"allowed": True, "reasons": reasons}
    
    if user_role == "manager" and user_department == resource_department:
        reasons.append("Manager can access resources in their department")
        return {"allowed": True, "reasons": reasons}
    
    if user_role == "user" and user_id == resource_owner_id:
        reasons.append("User can access their own resources")
        return {"allowed": True, "reasons": reasons}
    
    reasons.append("No applicable rule allows this access")
    return {"allowed": False, "reasons": reasons}
