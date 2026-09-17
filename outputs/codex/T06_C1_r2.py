def evaluate_access(user, resource, action, policy) -> dict:
    denied = {"allowed": False, "reasons": ["Access denied."]}

    try:
        if not isinstance(user, dict) or not isinstance(resource, dict) or not isinstance(policy, dict):
            return denied

        required_user = {"id", "role", "department", "status", "permissions"}
        required_resource = {"owner_id", "department", "classification"}
        required_policy = {"actions", "rules", "required_permissions"}

        if not required_user.issubset(user) or not required_resource.issubset(resource):
            return denied
        if not required_policy.issubset(policy):
            return denied

        if (
            not isinstance(user["role"], str)
            or user["role"] not in {"user", "manager", "administrator"}
            or not isinstance(user["status"], str)
            or user["status"] not in {"active", "inactive"}
            or not isinstance(user["permissions"], list)
            or not all(isinstance(permission, str) for permission in user["permissions"])
            or not isinstance(user["department"], str)
            or not isinstance(resource["department"], str)
            or not isinstance(resource["classification"], str)
            or resource["classification"] not in {"normal", "confidential"}
            or not isinstance(action, str)
        ):
            return denied

        if user["status"] == "inactive":
            return denied

        actions = policy["actions"]
        required_permissions = policy["required_permissions"]
        rules = policy["rules"]

        if (
            not isinstance(actions, list)
            or not all(isinstance(item, str) for item in actions)
            or not isinstance(required_permissions, dict)
            or not isinstance(rules, list)
        ):
            return denied

        if action not in actions:
            return denied

        classification = resource["classification"]
        if classification not in required_permissions:
            return denied

        required_permission = required_permissions[classification]
        if (
            not isinstance(required_permission, str)
            or required_permission not in user["permissions"]
        ):
            return denied

        valid_rule_keys = {"effect", "role", "action", "classification"}
        matching_denies = False
        matching_allows = False

        for rule in rules:
            if not isinstance(rule, dict) or not set(rule).issubset(valid_rule_keys):
                return denied
            if "effect" not in rule or rule["effect"] not in {"allow", "deny"}:
                return denied

            if "role" in rule and (
                not isinstance(rule["role"], str)
                or rule["role"] not in {"user", "manager", "administrator"}
            ):
                return denied
            if "action" in rule and not isinstance(rule["action"], str):
                return denied
            if "classification" in rule and (
                not isinstance(rule["classification"], str)
                or rule["classification"] not in {"normal", "confidential"}
            ):
                return denied

            matches = (
                ("role" not in rule or rule["role"] == user["role"])
                and ("action" not in rule or rule["action"] == action)
                and (
                    "classification" not in rule
                    or rule["classification"] == classification
                )
            )

            if matches:
                if rule["effect"] == "deny":
                    matching_denies = True
                else:
                    matching_allows = True

        if matching_denies:
            return denied

        if matching_allows:
            return {"allowed": True, "reasons": ["Allowed by policy rule."]}

        if user["role"] == "administrator":
            return {"allowed": True, "reasons": ["Allowed by administrator role."]}

        if user["role"] == "manager" and user["department"] == resource["department"]:
            return {"allowed": True, "reasons": ["Allowed by department access."]}

        if user["id"] == resource["owner_id"]:
            return {"allowed": True, "reasons": ["Allowed by resource ownership."]}

        return denied
    except Exception:
        return denied