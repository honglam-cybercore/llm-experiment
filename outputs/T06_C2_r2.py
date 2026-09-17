def _rule_matches(rule, user, resource, action):
    if "role" in rule and rule["role"] != user["role"]:
        return False
    if "action" in rule and rule["action"] != action:
        return False
    if "classification" in rule and rule["classification"] != resource["classification"]:
        return False
    return True


def evaluate_access(user, resource, action, policy) -> dict:
    reasons = []
    
    if not isinstance(user, dict) or not isinstance(resource, dict) or not isinstance(policy, dict):
        reasons.append("Invalid input types")
        return {"allowed": False, "reasons": reasons}
    
    if not isinstance(action, str):
        reasons.append("Action must be a string")
        return {"allowed": False, "reasons": reasons}
    
    if not all(k in user for k in ["id", "role", "department", "status", "permissions"]):
        reasons.append("User missing required fields")
        return {"allowed": False, "reasons": reasons}
    
    if not all(k in resource for k in ["owner_id", "department", "classification"]):
        reasons.append("Resource missing required fields")
        return {"allowed": False, "reasons": reasons}
    
    if not all(k in policy for k in ["actions", "rules", "required_permissions"]):
        reasons.append("Policy missing required fields")
        return {"allowed": False, "reasons": reasons}
    
    if not isinstance(user.get("permissions"), list):
        reasons.append("User permissions must be a list")
        return {"allowed": False, "reasons": reasons}
    
    if not isinstance(policy.get("actions"), list):
        reasons.append("Policy actions must be a list")
        return {"allowed": False, "reasons": reasons}
    
    if not isinstance(policy.get("rules"), list):
        reasons.append("Policy rules must be a list")
        return {"allowed": False, "reasons": reasons}
    
    if not isinstance(policy.get("required_permissions"), dict):
        reasons.append("Policy required_permissions must be a dict")
        return {"allowed": False, "reasons": reasons}
    
    if user.get("status") != "active":
        reasons.append("User is not active")
        return {"allowed": False, "reasons": reasons}
    
    if action not in policy["actions"]:
        reasons.append("Action not defined in policy")
        return {"allowed": False, "reasons": reasons}
    
    if user.get("role") not in ["user", "manager", "administrator"]:
        reasons.append("Unknown role")
        return {"allowed": False, "reasons": reasons}
    
    if resource.get("classification") not in ["normal", "confidential"]:
        reasons.append("Unknown classification")
        return {"allowed": False, "reasons": reasons}
    
    classification = resource.get("classification")
    required_perms = policy["required_permissions"]
    if classification in required_perms:
        required_perm = required_perms[classification]
        if required_perm not in user["permissions"]:
            reasons.append(f"Missing required permission for {classification} resource")
            return {"allowed": False, "reasons": reasons}
    
    for rule in policy["rules"]:
        if not isinstance(rule, dict):
            continue
        if rule.get("effect") == "deny" and _rule_matches(rule, user, resource, action):
            reasons.append("Matched explicit deny rule")
            return {"allowed": False, "reasons": reasons}
    
    for rule in policy["rules"]:
        if not isinstance(rule, dict):
            continue
        if rule.get("effect") == "allow" and _rule_matches(rule, user, resource, action):
            reasons.append("Matched allow rule")
            return {"allowed": True, "reasons": reasons}
    
    role = user["role"]
    if role == "administrator":
        reasons.append("Administrator has access to all resources")
        return {"allowed": True, "reasons": reasons}
    
    if role == "manager":
        if user["department"] == resource["department"]:
            reasons.append("Manager has access to department resources")
            return {"allowed": True, "reasons": reasons}
    
    if role == "user":
        if user["id"] == resource["owner_id"]:
            reasons.append("User has access to own resources")
            return {"allowed": True, "reasons": reasons}
    
    reasons.append("No applicable access rule found")
    return {"allowed": False, "reasons": reasons}
