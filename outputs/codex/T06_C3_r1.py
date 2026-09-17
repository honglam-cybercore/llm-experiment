def evaluate_access(user, resource, action, policy) -> dict:
    def denied(reason):
        return {"allowed": False, "reasons": [reason]}

    try:
        if not isinstance(user, dict) or not isinstance(resource, dict) or not isinstance(policy, dict):
            return denied("malformed input")

        required_user = {"id", "role", "department", "status", "permissions"}
        required_resource = {"owner_id", "department", "classification"}
        required_policy = {"actions", "rules", "required_permissions"}

        if not required_user.issubset(user):
            return denied("malformed user")
        if not required_resource.issubset(resource):
            return denied("malformed resource")
        if not required_policy.issubset(policy):
            return denied("malformed policy")

        role = user["role"]
        status = user["status"]
        classification = resource["classification"]

        if not isinstance(role, str) or role not in {"user", "manager", "administrator"}:
            return denied("unknown role")
        if not isinstance(status, str) or status not in {"active", "inactive"}:
            return denied("malformed account status")
        if status != "active":
            return denied("inactive account")
        if not isinstance(action, str):
            return denied("malformed action")
        if classification not in {"normal", "confidential"}:
            return denied("unknown classification")
        if not isinstance(user["permissions"], list) or not all(
            isinstance(permission, str) for permission in user["permissions"]
        ):
            return denied("malformed permissions")

        actions = policy["actions"]
        if not isinstance(actions, list) or not all(
            isinstance(policy_action, str) for policy_action in actions
        ):
            return denied("malformed policy actions")
        if action not in actions:
            return denied("action is not defined by policy")

        required_permissions = policy["required_permissions"]
        if not isinstance(required_permissions, dict):
            return denied("malformed required permissions")
        for key, permission in required_permissions.items():
            if key not in {"normal", "confidential"} or not isinstance(permission, str):
                return denied("malformed required permissions")

        required_permission = required_permissions.get(classification)
        if required_permission is not None and required_permission not in user["permissions"]:
            return denied("required permission missing")

        rules = policy["rules"]
        if not isinstance(rules, list):
            return denied("malformed policy rules")

        for rule in rules:
            if not isinstance(rule, dict) or "effect" not in rule:
                return denied("malformed policy rule")
            if rule["effect"] not in {"allow", "deny"}:
                return denied("malformed policy rule")

            allowed_keys = {"effect", "role", "action", "classification"}
            if any(key not in allowed_keys for key in rule):
                return denied("malformed policy rule")

            if "role" in rule and (
                not isinstance(rule["role"], str)
                or rule["role"] not in {"user", "manager", "administrator"}
            ):
                return denied("malformed policy rule")
            if "action" in rule and not isinstance(rule["action"], str):
                return denied("malformed policy rule")
            if "classification" in rule and (
                not isinstance(rule["classification"], str)
                or rule["classification"] not in {"normal", "confidential"}
            ):
                return denied("malformed policy rule")

        def matches(rule):
            return (
                ("role" not in rule or rule["role"] == role)
                and ("action" not in rule or rule["action"] == action)
                and (
                    "classification" not in rule
                    or rule["classification"] == classification
                )
            )

        for rule in rules:
            if rule["effect"] == "deny" and matches(rule):
                return denied("denied by policy rule")

        for rule in rules:
            if rule["effect"] == "allow" and matches(rule):
                return {"allowed": True, "reasons": ["allowed by policy rule"]}

        if role == "administrator":
            return {"allowed": True, "reasons": ["administrator access"]}
        if role == "manager" and user["department"] == resource["department"]:
            return {"allowed": True, "reasons": ["manager access in own department"]}
        if role not in {"manager", "administrator"} and user["id"] == resource["owner_id"]:
            return {"allowed": True, "reasons": ["resource ownership"]}

        return denied("not authorized by built-in rules")
    except BaseException:
        return denied("malformed input")