def evaluate_access(user, resource, action, policy) -> dict:
    def deny(reason):
        return {"allowed": False, "reasons": [reason]}

    try:
        if not isinstance(user, dict) or not isinstance(resource, dict) or not isinstance(policy, dict):
            return deny("Malformed input")

        required_user = ("id", "role", "department", "status", "permissions")
        required_resource = ("owner_id", "department", "classification")
        required_policy = ("actions", "rules", "required_permissions")

        if any(key not in user for key in required_user):
            return deny("Missing user field")
        if any(key not in resource for key in required_resource):
            return deny("Missing resource field")
        if any(key not in policy for key in required_policy):
            return deny("Missing policy field")

        role = user["role"]
        status = user["status"]
        classification = resource["classification"]

        if not isinstance(role, str) or role not in {"user", "manager", "administrator"}:
            return deny("Unknown role")
        if status != "active":
            return deny("Inactive account")
        if not isinstance(action, str):
            return deny("Malformed action")

        actions = policy["actions"]
        if not isinstance(actions, list) or any(not isinstance(item, str) for item in actions):
            return deny("Malformed policy actions")
        if action not in actions:
            return deny("Action is not defined by policy")

        if not isinstance(classification, str) or classification not in {"normal", "confidential"}:
            return deny("Unknown classification")

        permissions = user["permissions"]
        if not isinstance(permissions, list) or any(not isinstance(item, str) for item in permissions):
            return deny("Malformed permissions")

        required_permissions = policy["required_permissions"]
        if not isinstance(required_permissions, dict):
            return deny("Malformed required permissions")

        for key, permission in required_permissions.items():
            if key not in {"normal", "confidential"} or not isinstance(permission, str):
                return deny("Malformed required permissions")

        if classification in required_permissions:
            required = required_permissions[classification]
            if required not in permissions:
                return deny("Required permission is missing")

        rules = policy["rules"]
        if not isinstance(rules, list):
            return deny("Malformed policy rules")

        valid_rule_keys = {"effect", "role", "action", "classification"}
        matching_allows = []

        for rule in rules:
            if not isinstance(rule, dict):
                return deny("Malformed policy rule")
            if any(key not in valid_rule_keys for key in rule):
                return deny("Malformed policy rule")
            if "effect" not in rule or rule["effect"] not in {"allow", "deny"}:
                return deny("Malformed policy rule")

            if "role" in rule and (
                not isinstance(rule["role"], str)
                or rule["role"] not in {"user", "manager", "administrator"}
            ):
                return deny("Malformed policy rule")
            if "action" in rule and (
                not isinstance(rule["action"], str)
                or rule["action"] not in actions
            ):
                return deny("Malformed policy rule")
            if "classification" in rule and (
                not isinstance(rule["classification"], str)
                or rule["classification"] not in {"normal", "confidential"}
            ):
                return deny("Malformed policy rule")

            matches = all(
                rule[key] == value
                for key, value in (
                    ("role", role),
                    ("action", action),
                    ("classification", classification),
                )
                if key in rule
            )

            if matches:
                if rule["effect"] == "deny":
                    return deny("Denied by policy rule")
                matching_allows.append(rule)

        if matching_allows:
            return {"allowed": True, "reasons": ["Allowed by policy rule"]}

        if role == "administrator":
            return {"allowed": True, "reasons": ["Administrator access"]}
        if role == "manager" and user["department"] == resource["department"]:
            return {"allowed": True, "reasons": ["Manager access within department"]}
        if user["id"] == resource["owner_id"]:
            return {"allowed": True, "reasons": ["Resource ownership"]}

        return deny("Denied by built-in access rules")
    except Exception:
        return deny("Malformed input")