def evaluate_access(user, resource, action, policy) -> dict:
    reasons = []
    
    try:
        # Validate input structure
        if not isinstance(user, dict) or not isinstance(resource, dict) or not isinstance(action, str) or not isinstance(policy, dict):
            return {"allowed": False, "reasons": ["Invalid input structure"]}
        
        # Check required fields
        if not all(key in user for key in ["id", "role", "department", "status", "permissions"]):
            return {"allowed": False, "reasons": ["Missing required user fields"]}
        
        if not all(key in resource for key in ["owner_id", "department", "classification"]):
            return {"allowed": False, "reasons": ["Missing required resource fields"]}
        
        if not all(key in policy for key in ["actions", "rules", "required_permissions"]):
            return {"allowed": False, "reasons": ["Missing required policy fields"]}
        
        # Validate collection types
        if not isinstance(user["permissions"], list):
            return {"allowed": False, "reasons": ["User permissions must be a list"]}
        
        if not isinstance(policy["actions"], list):
            return {"allowed": False, "reasons": ["Policy actions must be a list"]}
        
        if not isinstance(policy["rules"], list):
            return {"allowed": False, "reasons": ["Policy rules must be a list"]}
        
        if not isinstance(policy["required_permissions"], dict):
            return {"allowed": False, "reasons": ["Policy required_permissions must be a dict"]}
        
        # Validate permissions are strings
        if not all(isinstance(p, str) for p in user["permissions"]):
            return {"allowed": False, "reasons": ["Invalid user permissions format"]}
        
        # Validate actions are strings
        if not all(isinstance(a, str) for a in policy["actions"]):
            return {"allowed": False, "reasons": ["Invalid policy actions format"]}
        
        # Validate required_permissions values are strings
        if not all(isinstance(v, str) for v in policy["required_permissions"].values()):
            return {"allowed": False, "reasons": ["Invalid required permissions format"]}
        
        # Check if user is inactive
        if user["status"] != "active":
            reasons.append("User is not active")
            return {"allowed": False, "reasons": reasons}
        
        # Check if action is defined in policy
        if action not in policy["actions"]:
            reasons.append("Action not in policy")
            return {"allowed": False, "reasons": reasons}
        
        # Check if role is valid
        if user["role"] not in ["user", "manager", "administrator"]:
            reasons.append("Unknown role")
            return {"allowed": False, "reasons": reasons}
        
        # Check if classification is valid
        if resource["classification"] not in ["normal", "confidential"]:
            reasons.append("Unknown classification")
            return {"allowed": False, "reasons": reasons}
        
        # Check required permissions
        classification = resource["classification"]
        if classification in policy["required_permissions"]:
            required_perm = policy["required_permissions"][classification]
            if required_perm not in user["permissions"]:
                reasons.append("Missing required permission")
                return {"allowed": False, "reasons": reasons}
        
        # Check policy rules
        deny_found = False
        allow_found = False
        
        for rule in policy["rules"]:
            if not isinstance(rule, dict):
                continue
            
            # Check if rule matches
            matches = True
            if "role" in rule and rule["role"] != user["role"]:
                matches = False
            if "action" in rule and rule["action"] != action:
                matches = False
            if "classification" in rule and rule["classification"] != classification:
                matches = False
            
            if matches:
                if rule.get("effect") == "deny":
                    deny_found = True
                elif rule.get("effect") == "allow":
                    allow_found = True
        
        if deny_found:
            reasons.append("Denied by policy rule")
            return {"allowed": False, "reasons": reasons}
        
        if allow_found:
            reasons.append("Allowed by policy rule")
            return {"allowed": True, "reasons": reasons}
        
        # Apply built-in rules
        if user["role"] == "administrator":
            reasons.append("Allowed by built-in rule: administrator")
            return {"allowed": True, "reasons": reasons}
        
        if user["role"] == "manager" and user["department"] == resource["department"]:
            reasons.append("Allowed by built-in rule: manager")
            return {"allowed": True, "reasons": reasons}
        
        if user["id"] == resource["owner_id"]:
            reasons.append("Allowed by built-in rule: owner")
            return {"allowed": True, "reasons": reasons}
        
        # Default deny
        reasons.append("No matching allow rule")
        return {"allowed": False, "reasons": reasons}
        
    except Exception:
        return {"allowed": False, "reasons": ["Evaluation error"]}
