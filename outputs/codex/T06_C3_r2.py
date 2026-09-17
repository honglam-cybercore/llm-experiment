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

        user_id = user["id"]
        role = user["role"]
        user_department = user["department"]
        status = user["status"]
        permissions = user["permissions"]

        owner_id = resource["owner_id"]
        resource_department = resource["department"]
        classification = resource["classification"]

        actions = policy["actions"]
        rules = policy["rules"]
        required_permissions = policy["required_permissions"]

        if not isinstance(user_id, str) or not isinstance(owner_id, str):
            return denied
        if not isinstance(user_department, str) or not isinstance(resource_department, str):
            return denied
        if not isinstance(role, str) or role not in {"user", "manager", "administrator"}:
            return denied
        if not isinstance(status, str) or status not in {"active", "inactive"}:
            return denied
        if status != "active":
            return {"allowed": False, "reasons": ["Inactive account."]}

        if not isinstance(permissions, list) or any(not isinstance(p, str) for p in permissions):
            return denied
        if not isinstance(classification, str) or classification not in {"normal", "confidential"}:
            return denied
        if not isinstance(action, str):
            return denied

        if not isinstance(actions, list) or any(not isinstance(a, str) for a in actions):
            return denied
        if action not in actions:
            return {"allowed": False, "reasons": ["Action is not defined by policy."]}

        if not isinstance(required_permissions, dict):
            return denied
        for key, permission in required_permissions.items():
            if key not in {"normal", "confidential"} or not isinstance(permission, str):
                return denied

        required_permission = required_permissions.get(classification)
        if required_permission is not None and required_permission not in permissions:
            return {"allowed": False, "reasons": ["Required permission is missing."]}

        if not isinstance(rules, list):
            return denied

        matching_denies = False
        matching_allows = False
        valid_rule_keys = {"effect", "role", "action", "classification"}

        for rule in rules:
            if not isinstance(rule, dict) or "effect" not in rule:
                return denied
            if any(key not in valid_rule_keys for key in rule):
                return denied
            if rule["effect"] not in {"allow", "deny"}:
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

            matches = all(
                (
                    key == "effect"
                    or rule[key] == {
                        "role": role,
                        "action": action,
                        "classification": classification,
                    }[key]
                )
                for key in rule
            )

            if matches:
                if rule["effect"] == "deny":
                    matching_denies = True
                else:
                    matching_allows = True

        if matching_denies:
            return {"allowed": False, "reasons": ["Denied by policy rule."]}
        if matching_allows:
            return {"allowed": True, "reasons": ["Allowed by policy rule."]}

        built_in_allowed = (
            role == "administrator"
            or (role == "manager" and user_department == resource_department)
            or (role == "user" and user_id == owner_id)
        )

        if built_in_allowed:
            return {"allowed": True, "reasons": ["Allowed by built-in access rules."]}

        return {"allowed": False, "reasons": ["Access denied by built-in access rules."]}

    except BaseException:
        return denied