def evaluate_access(user, resource, action, policy) -> dict:
    reasons = []
    
    try:
        # Validate types of top-level objects
        if not isinstance(user, dict):
            return {"allowed": False, "reasons": ["Invalid user"]}
        if not isinstance(resource, dict):
            return {"allowed": False, "reasons": ["Invalid resource"]}
        if not isinstance(action, str):
            return {"allowed": False, "reasons": ["Invalid action"]}
        if not isinstance(policy, dict):
            return {"allowed": False, "reasons": ["Invalid policy"]}
        
        # Extract user fields
        user_id = user.get("id")
        user_role = user.get("role")
        user_department = user.get("department")
        user_status = user.get("status")
        user_permissions = user.get("permissions", [])
        
        # Validate user fields
        if not isinstance(user_id, str):
            return {"allowed": False, "reasons": ["Invalid user id"]}
        if not isinstance(user_permissions, list):
            return {"allowed": False, "reasons": ["Invalid user permissions"]}
        
        # Extract resource fields
        resource_owner_id = resource.get("owner_id")
        resource_department = resource.get("department")
        resource_classification = resource.get("classification")
        
        # Validate resource fields
        if not isinstance(resource_owner_id, str):
            return {"allowed": False, "reasons": ["Invalid resource owner_id"]}
        if not isinstance(resource_department, str):
            return {"allowed": False, "reasons": ["Invalid resource department"]}
        
        # Extract policy fields
        policy_actions = policy.get("actions", [])
        policy_rules = policy.get("rules", [])
        required_permissions = policy.get("required_permissions", {})
        
        # Validate policy fields
        if not isinstance(policy_actions, list):
            return {"allowed": False, "reasons": ["Invalid policy actions"]}
        if not isinstance(policy_rules, list):
            return {"allowed": False, "reasons": ["Invalid policy rules"]}
        if not isinstance(required_permissions, dict):
            return {"allowed": False, "reasons": ["Invalid policy required_permissions"]}
        
        # Immediate denial checks
        
        # 1. Check if account is active
        if user_status != "active":
            reasons.append("User account is not active")
            return {"allowed": False, "reasons": reasons}
        
        # 2. Check if action is defined in policy
        if action not in policy_actions:
            reasons.append("Action not defined in policy")
            return {"allowed": False, "reasons": reasons}
        
        # 3. Check if role is known
        valid_roles = {"user", "manager", "administrator"}
        if user_role not in valid_roles:
            reasons.append("Unknown user role")
            return {"allowed": False, "reasons": reasons}
        
        # 4. Check if classification is known
        valid_classifications = {"normal", "confidential"}
        if resource_classification not in valid_classifications:
            reasons.append("Unknown resource classification")
            return {"allowed": False, "reasons": reasons}
        
        # 5. Check if user has required permissions
        if resource_classification in required_permissions:
            required_perm = required_permissions[resource_classification]
            if required_perm not in user_permissions:
                reasons.append("User lacks required permission")
                return {"allowed": False, "reasons": reasons}
        
        # Check deny rules
        for rule in policy_rules:
            if not isinstance(rule, dict):
                continue
            
            effect = rule.get("effect")
            if effect != "deny":
                continue
            
            # Check if rule matches
            matches = True
            if "role" in rule and rule["role"] != user_role:
                matches = False
            if "action" in rule and rule["action"] != action:
                matches = False
            if "classification" in rule and rule["classification"] != resource_classification:
                matches = False
            
            if matches:
                reasons.append("Denied by policy rule")
                return {"allowed": False, "reasons": reasons}
        
        # Check allow rules
        for rule in policy_rules:
            if not isinstance(rule, dict):
                continue
            
            effect = rule.get("effect")
            if effect != "allow":
                continue
            
            # Check if rule matches
            matches = True
            if "role" in rule and rule["role"] != user_role:
                matches = False
            if "action" in rule and rule["action"] != action:
                matches = False
            if "classification" in rule and rule["classification"] != resource_classification:
                matches = False
            
            if matches:
                reasons.append("Allowed by policy rule")
                return {"allowed": True, "reasons": reasons}
        
        # Apply built-in rules
        if user_role == "administrator":
            reasons.append("Administrator role allows access")
            return {"allowed": True, "reasons": reasons}
        elif user_role == "manager":
            if user_department == resource_department:
                reasons.append("Manager can access resources in own department")
                return {"allowed": True, "reasons": reasons}
            else:
                reasons.append("Manager cannot access resources outside own department")
                return {"allowed": False, "reasons": reasons}
        else:  # user role
            if user_id == resource_owner_id:
                reasons.append("User can access owned resources")
                return {"allowed": True, "reasons": reasons}
            else:
                reasons.append("User can only access owned resources")
                return {"allowed": False, "reasons": reasons}
    
    except Exception:
        return {"allowed": False, "reasons": ["Access denied"]}
