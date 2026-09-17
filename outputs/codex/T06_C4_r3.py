def evaluate_access(user, resource, action, policy) -> dict:
    def deny(reason):
        return {"allowed": False, "reasons": [reason]}

    try:
        if not isinstance(user, dict) or not isinstance(resource, dict) or not isinstance(policy, dict):
            return deny("malformed input")

        required_user = ("id", "role", "department", "status", "permissions")
        required_resource = ("owner_id", "department", "classification")
        required_policy = ("actions", "rules", "required_permissions")

        if any(key not in user for key in required_user):
            return deny("missing user information")
        if any(key not in resource for key in required_resource):
            return deny("missing resource information")
        if any(key not in policy for key in required_policy):
            return deny("missing policy information")

        if (
            not isinstance(user["id"], str)
            or not user["id"]
            or not isinstance(user["role"], str)
            or not isinstance(user["department"], str)
            or not user["department"]
            or user["status"] not in {"active", "inactive"}
            or not isinstance(user["permissions"], list)
            or any(not isinstance(permission, str) for permission in user["permissions"])
        ):
            return deny("malformed user")

        if (
            not isinstance(resource["owner_id"], str)
            or not resource["owner_id"]
            or not isinstance(resource["department"], str)
            or not resource["department"]
            or resource["classification"] not in {"normal", "confidential"}
        ):
            return deny("malformed resource")

        if not isinstance(action, str) or not action:
            return deny("malformed action")

        actions = policy["actions"]
        rules = policy["rules"]
        required_permissions = policy["required_permissions"]

        if (
            not isinstance(actions, list)
            or any(not isinstance(item, str) or not item for item in actions)
            or not isinstance(rules, list)
            or not isinstance(required_permissions, dict)
        ):
            return deny("malformed policy")

        for classification, permission in required_permissions.items():
            if (
                classification not in {"normal", "confidential"}
                or not isinstance(permission, str)
                or not permission
            ):
                return deny("malformed policy")

        if user["status"] != "active":
            return deny("inactive account")

        if user["role"] not in {"user", "manager", "administrator"}:
            return deny("unknown role")

        if action not in actions:
            return deny("action is not defined by policy")

        classification = resource["classification"]

        if classification == "confidential" and classification not in required_permissions:
            return deny("missing required permission policy")

        required_permission = required_permissions.get(classification)
        if required_permission is not None and required_permission not in user["permissions"]:
            return deny("required permission missing")

        valid_rules = []
        for rule in rules:
            if not isinstance(rule, dict) or "effect" not in rule:
                return deny("malformed policy rule")

            if set(rule) - {"effect", "role", "action", "classification"}:
                return deny("malformed policy rule")

            if rule["effect"] not in {"allow", "deny"}:
                return deny("malformed policy rule")

            if "role" in rule and (
                not isinstance(rule["role"], str)
                or rule["role"] not in {"user", "manager", "administrator"}
            ):
                return deny("malformed policy rule")

            if "action" in rule and (
                not isinstance(rule["action"], str) or not rule["action"]
            ):
                return deny("malformed policy rule")

            if "classification" in rule and (
                rule["classification"] not in {"normal", "confidential"}
            ):
                return deny("malformed policy rule")

            valid_rules.append(rule)

        def matches(rule):
            return all(
                (
                    key == "effect"
                    or rule[key] == {
                        "role": user["role"],
                        "action": action,
                        "classification": classification,
                    }[key]
                )
                for key in rule
            )

        if any(rule["effect"] == "deny" and matches(rule) for rule in valid_rules):
            return deny("explicit deny rule")

        if any(rule["effect"] == "allow" and matches(rule) for rule in valid_rules):
            return {"allowed": True, "reasons": ["explicit allow rule"]}

        if user["role"] == "administrator":
            return {"allowed": True, "reasons": ["administrator access"]}

        if user["role"] == "manager" and user["department"] == resource["department"]:
            return {"allowed": True, "reasons": ["department manager access"]}

        if user["id"] == resource["owner_id"]:
            return {"allowed": True, "reasons": ["resource ownership"]}

        return deny("no applicable access rule")
    except Exception:
        return deny("malformed input")