def evaluate_access(user, resource, action, policy) -> dict:
    reasons = []
    
    try:
        # Validate basic structure
        if not isinstance(user, dict) or not isinstance(resource, dict) or not isinstance(policy, dict):
            return {"allowed": False, "reasons": ["Invalid input structure"]}
        
        # Check required fields
        if not all(field in user for field in {"id", "role", "department", "status", "permissions"}):
            return {"allowed": False, "reasons": ["Missing required user fields"]}
        
        if not all(field in resource for field in {"owner_id", "department", "classification"}):
            return {"allowed": False, "reasons": ["Missing required resource fields"]}
        
        if not all(field in policy for field in {"actions", "rules", "required_permissions"}):
            return {"allowed": False, "reasons": ["Missing required policy fields"]}
        
        # Validate types
        if not isinstance(policy.get("actions"), list):
            return {"allowed": False, "reasons": ["Invalid policy actions"]}
        
        if not isinstance(policy.get("rules"), list):
            return {"allowed": False, "reasons": ["Invalid policy rules"]}
        
        if not isinstance(policy.get("required_permissions"), dict):
            return {"allowed": False, "reasons": ["Invalid policy required_permissions"]}
        
        if not isinstance(user.get("permissions"), list):
            return {"allowed": False, "reasons": ["Invalid user permissions"]}
        
        if not isinstance(action, str):
            return {"allowed": False, "reasons": ["Invalid action type"]}
        
        # Check 1: Account must be active
        if user.get("status") != "active":
            reasons.append("User account is not active")
            return {"allowed": False, "reasons": reasons}
        
        # Check 2: Action must be defined in policy
        if action not in policy.get("actions", []):
            reasons.append("Action not defined in policy")
            return {"allowed": False, "reasons": reasons}
        
        # Check 3: Role must be valid
        valid_roles = {"user", "manager", "administrator"}
        if user.get("role") not in valid_roles:
            reasons.append("Unknown role")
            return {"allowed": False, "reasons": reasons}
        
        # Check 4: Classification must be valid
        valid_classifications = {"normal", "confidential"}
        if resource.get("classification") not in valid_classifications:
            reasons.append("Unknown classification")
            return {"allowed": False, "reasons": reasons}
        
        # Check 5: User must have required permission for classification
        classification = resource.get("classification")
        required_permissions = policy.get("required_permissions", {})
        if classification in required_permissions:
            required_perm = required_permissions[classification]
            if required_perm not in user.get("permissions", []):
                reasons.append("Required permission not held")
                return {"allowed": False, "reasons": reasons}
        
        # Check deny rules
        for rule in policy.get("rules", []):
            if not isinstance(rule, dict):
                continue
            
            if rule.get("effect") == "deny" and _matches_rule(user, resource, action, rule):
                reasons.append("Denied by policy rule")
                return {"allowed": False, "reasons": reasons}
        
        # Check allow rules
        for rule in policy.get("rules", []):
            if not isinstance(rule, dict):
                continue
            
            if rule.get("effect") == "allow" and _matches_rule(user, resource, action, rule):
                reasons.append("Allowed by policy rule")
                return {"allowed": True, "reasons": reasons}
        
        # Apply built-in rules
        role = user.get("role")
        
        if role == "administrator":
            reasons.append("Administrator can perform any action")
            return {"allowed": True, "reasons": reasons}
        
        if role == "manager":
            if user.get("department") == resource.get("department"):
                reasons.append("Manager can act on resources in their department")
                return {"allowed": True, "reasons": reasons}
            else:
                reasons.append("Manager can only act on resources in their department")
                return {"allowed": False, "reasons": reasons}
        
        # role == "user"
        if user.get("id") == resource.get("owner_id"):
            reasons.append("User can act on owned resources")
            return {"allowed": True, "reasons": reasons}
        else:
            reasons.append("User can only act on owned resources")
            return {"allowed": False, "reasons": reasons}
    
    except Exception:
        return {"allowed": False, "reasons": ["Evaluation error"]}


def _matches_rule(user, resource, action, rule):
    if "role" in rule and user.get("role") != rule["role"]:
        return False
    if "action" in rule and action != rule["action"]:
        return False
    if "classification" in rule and resource.get("classification") != rule["classification"]:
        return False
    return True
