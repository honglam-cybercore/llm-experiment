def evaluate_access(user, resource, action, policy) -> dict:
    try:
        # Validate input types
        if not isinstance(user, dict) or not isinstance(resource, dict):
            return {"allowed": False, "reasons": ["Invalid input"]}
        if not isinstance(action, str) or not action:
            return {"allowed": False, "reasons": ["Invalid action"]}
        if not isinstance(policy, dict):
            return {"allowed": False, "reasons": ["Invalid policy"]}
        
        # Extract user fields
        user_id = user.get("id")
        user_role = user.get("role")
        user_department = user.get("department")
        user_status = user.get("status")
        user_permissions = user.get("permissions", [])
        
        # Extract resource fields
        owner_id = resource.get("owner_id")
        resource_department = resource.get("department")
        resource_classification = resource.get("classification")
        
        # Extract policy fields
        policy_actions = policy.get("actions", [])
        policy_rules = policy.get("rules", [])
        required_permissions = policy.get("required_permissions", {})
        
        # Validate collection types
        if not isinstance(user_permissions, list):
            return {"allowed": False, "reasons": ["Invalid permissions"]}
        if not isinstance(policy_actions, list):
            return {"allowed": False, "reasons": ["Invalid actions"]}
        if not isinstance(policy_rules, list):
            return {"allowed": False, "reasons": ["Invalid rules"]}
        if not isinstance(required_permissions, dict):
            return {"allowed": False, "reasons": ["Invalid required permissions"]}
        
        reasons = []
        
        # Check account status
        if user_status != "active":
            reasons.append("User account not active")
            return {"allowed": False, "reasons": reasons}
        
        # Check action defined in policy
        if action not in policy_actions:
            reasons.append("Action not defined in policy")
            return {"allowed": False, "reasons": reasons}
        
        # Check role is known
        if user_role not in {"user", "manager", "administrator"}:
            reasons.append("Unknown user role")
            return {"allowed": False, "reasons": reasons}
        
        # Check classification is known
        if resource_classification not in {"normal", "confidential"}:
            reasons.append("Unknown resource classification")
            return {"allowed": False, "reasons": reasons}
        
        # Check required permissions for classification
        if resource_classification in required_permissions:
            required_perm = required_permissions[resource_classification]
            if required_perm not in user_permissions:
                reasons.append("Missing required permission")
                return {"allowed": False, "reasons": reasons}
        
        # Check explicit deny rules
        for rule in policy_rules:
            if not isinstance(rule, dict):
                continue
            if rule.get("effect") != "deny":
                continue
            if _rule_matches(rule, user_role, action, resource_classification):
                reasons.append("Denied by policy rule")
                return {"allowed": False, "reasons": reasons}
        
        # Check explicit allow rules
        for rule in policy_rules:
            if not isinstance(rule, dict):
                continue
            if rule.get("effect") != "allow":
                continue
            if _rule_matches(rule, user_role, action, resource_classification):
                reasons.append("Allowed by policy rule")
                return {"allowed": True, "reasons": reasons}
        
        # Apply built-in rules
        if user_role == "administrator":
            reasons.append("Allowed as administrator")
            return {"allowed": True, "reasons": reasons}
        
        if user_role == "manager" and user_department is not None and resource_department is not None and user_department == resource_department:
            reasons.append("Allowed as manager in own department")
            return {"allowed": True, "reasons": reasons}
        
        if user_role == "user" and user_id is not None and owner_id is not None and user_id == owner_id:
            reasons.append("Allowed as resource owner")
            return {"allowed": True, "reasons": reasons}
        
        reasons.append("Access denied")
        return {"allowed": False, "reasons": reasons}
    
    except Exception:
        return {"allowed": False, "reasons": ["Access evaluation error"]}


def _rule_matches(rule, user_role, action, resource_classification):
    if "role" in rule and rule["role"] != user_role:
        return False
    if "action" in rule and rule["action"] != action:
        return False
    if "classification" in rule and rule["classification"] != resource_classification:
        return False
    return True
