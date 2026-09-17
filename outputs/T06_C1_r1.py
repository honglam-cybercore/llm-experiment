def evaluate_access(user, resource, action, policy) -> dict:
    reasons = []
    
    try:
        # Input validation
        if not isinstance(user, dict) or not isinstance(resource, dict) or not isinstance(policy, dict):
            return {"allowed": False, "reasons": ["Invalid input types"]}
        
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
        policy_required_permissions = policy.get("required_permissions", {})
        
        # Check for missing required fields
        if (user_id is None or user_role is None or user_department is None or 
            user_status is None or owner_id is None or resource_department is None or 
            resource_classification is None):
            return {"allowed": False, "reasons": ["Missing required fields"]}
        
        # Ensure permissions is a list
        if not isinstance(user_permissions, list):
            user_permissions = []
        
        # Outright denial checks
        
        # Check 1: Account status must be "active"
        if user_status != "active":
            reasons.append("User account is not active")
            return {"allowed": False, "reasons": reasons}
        
        # Check 2: Action must be defined in policy
        if action not in policy_actions:
            reasons.append("Action not defined in policy")
            return {"allowed": False, "reasons": reasons}
        
        # Check 3: Role must be valid
        valid_roles = {"user", "manager", "administrator"}
        if user_role not in valid_roles:
            reasons.append("Unknown role")
            return {"allowed": False, "reasons": reasons}
        
        # Check 4: Classification must be valid
        valid_classifications = {"normal", "confidential"}
        if resource_classification not in valid_classifications:
            reasons.append("Unknown classification")
            return {"allowed": False, "reasons": reasons}
        
        # Check 5: User must have required permission for classification
        required_permission = policy_required_permissions.get(resource_classification)
        if required_permission is not None and required_permission not in user_permissions:
            reasons.append("Missing required permission")
            return {"allowed": False, "reasons": reasons}
        
        # Check policy rules
        if isinstance(policy_rules, list):
            # Check deny rules first
            for rule in policy_rules:
                if isinstance(rule, dict) and rule.get("effect") == "deny":
                    if _rule_matches(rule, user_role, action, resource_classification):
                        reasons.append("Denied by policy rule")
                        return {"allowed": False, "reasons": reasons}
            
            # Check allow rules
            for rule in policy_rules:
                if isinstance(rule, dict) and rule.get("effect") == "allow":
                    if _rule_matches(rule, user_role, action, resource_classification):
                        reasons.append("Allowed by policy rule")
                        return {"allowed": True, "reasons": reasons}
        
        # Apply built-in rules
        if user_role == "administrator":
            reasons.append("Allowed by built-in rule: administrator")
            return {"allowed": True, "reasons": reasons}
        
        if user_role == "manager":
            if user_department == resource_department:
                reasons.append("Allowed by built-in rule: manager in same department")
                return {"allowed": True, "reasons": reasons}
            else:
                reasons.append("Denied by built-in rule: manager not in same department")
                return {"allowed": False, "reasons": reasons}
        
        # For "user" role
        if user_id == owner_id:
            reasons.append("Allowed by built-in rule: user owns resource")
            return {"allowed": True, "reasons": reasons}
        else:
            reasons.append("Denied by built-in rule: user does not own resource")
            return {"allowed": False, "reasons": reasons}
    
    except Exception:
        return {"allowed": False, "reasons": ["Error evaluating access"]}


def _rule_matches(rule, user_role, action, resource_classification):
    if "role" in rule and rule["role"] != user_role:
        return False
    if "action" in rule and rule["action"] != action:
        return False
    if "classification" in rule and rule["classification"] != resource_classification:
        return False
    return True
