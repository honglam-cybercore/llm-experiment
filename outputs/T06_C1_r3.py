def evaluate_access(user, resource, action, policy) -> dict:
    try:
        # Validate types
        if not isinstance(user, dict):
            return {"allowed": False, "reasons": ["Invalid user"]}
        if not isinstance(resource, dict):
            return {"allowed": False, "reasons": ["Invalid resource"]}
        if not isinstance(action, str):
            return {"allowed": False, "reasons": ["Invalid action"]}
        if not isinstance(policy, dict):
            return {"allowed": False, "reasons": ["Invalid policy"]}
        
        # Validate and extract user
        if not all(k in user for k in ["id", "role", "department", "status", "permissions"]):
            return {"allowed": False, "reasons": ["User missing required fields"]}
        
        user_id = user["id"]
        user_role = user["role"]
        user_department = user["department"]
        user_status = user["status"]
        user_permissions = user["permissions"]
        
        if not isinstance(user_permissions, list):
            return {"allowed": False, "reasons": ["User permissions must be a list"]}
        
        # Validate and extract resource
        if not all(k in resource for k in ["owner_id", "department", "classification"]):
            return {"allowed": False, "reasons": ["Resource missing required fields"]}
        
        resource_owner_id = resource["owner_id"]
        resource_department = resource["department"]
        resource_classification = resource["classification"]
        
        # Validate and extract policy
        if not all(k in policy for k in ["actions", "rules", "required_permissions"]):
            return {"allowed": False, "reasons": ["Policy missing required fields"]}
        
        policy_actions = policy["actions"]
        policy_rules = policy["rules"]
        required_permissions = policy["required_permissions"]
        
        if not isinstance(policy_actions, list):
            return {"allowed": False, "reasons": ["Policy actions must be a list"]}
        if not isinstance(policy_rules, list):
            return {"allowed": False, "reasons": ["Policy rules must be a list"]}
        if not isinstance(required_permissions, dict):
            return {"allowed": False, "reasons": ["Policy required_permissions must be a dict"]}
        
        # Outright denials
        if user_status != "active":
            return {"allowed": False, "reasons": ["User account is not active"]}
        
        if action not in policy_actions:
            return {"allowed": False, "reasons": ["Action not defined in policy"]}
        
        if user_role not in ["user", "manager", "administrator"]:
            return {"allowed": False, "reasons": ["Unknown role"]}
        
        if resource_classification not in ["normal", "confidential"]:
            return {"allowed": False, "reasons": ["Unknown resource classification"]}
        
        if resource_classification in required_permissions:
            required_perm = required_permissions[resource_classification]
            if required_perm not in user_permissions:
                return {"allowed": False, "reasons": ["User lacks required permission for resource classification"]}
        
        # Check policy rules
        allow_matched = False
        
        for rule in policy_rules:
            if not isinstance(rule, dict):
                continue
            
            effect = rule.get("effect")
            if effect not in ["allow", "deny"]:
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
                if effect == "deny":
                    return {"allowed": False, "reasons": ["Access denied by policy rule"]}
                elif effect == "allow":
                    allow_matched = True
        
        if allow_matched:
            return {"allowed": True, "reasons": ["Access allowed by policy rule"]}
        
        # Apply built-in rules
        if user_role == "administrator":
            return {"allowed": True, "reasons": ["Access allowed: administrator"]}
        
        if user_role == "manager":
            if user_department == resource_department:
                return {"allowed": True, "reasons": ["Access allowed: manager in same department"]}
            else:
                return {"allowed": False, "reasons": ["Access denied: manager in different department"]}
        
        # user role
        if user_id == resource_owner_id:
            return {"allowed": True, "reasons": ["Access allowed: user is owner"]}
        else:
            return {"allowed": False, "reasons": ["Access denied: user is not owner"]}
    
    except Exception:
        return {"allowed": False, "reasons": ["Error evaluating access"]}
