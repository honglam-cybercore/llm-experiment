def evaluate_access(user, resource, action, policy) -> dict:
    def deny(reason):
        return {"allowed": False, "reasons": [reason]}

    try:
        if not isinstance(user, dict) or not isinstance(resource, dict) or not isinstance(policy, dict):
            return deny("malformed input")

        user_required = {"id", "role", "department", "status", "permissions"}
        resource_required = {"owner_id", "department", "classification"}
        policy_required = {"actions", "rules", "required_permissions"}

        if not user_required.issubset(user):
            return deny("missing user information")
        if not resource_required.issubset(resource):
            return deny("missing resource information")
        if not policy_required.issubset(policy):
            return deny("missing policy information")

        if user["status"] not in ("active", "inactive"):
            return deny("unknown account status")
        if user["status"] == "inactive":
            return deny("inactive account")

        if user["role"] not in ("user", "manager", "administrator"):
            return deny("unknown role")

        if not isinstance(user["permissions"], list) or not all(
            isinstance(permission, str) for permission in user["permissions"]
        ):
            return deny("malformed permissions")

        if not isinstance(action, str):
            return deny("unknown action")
        if not isinstance(policy["actions"], list) or not all(
            isinstance(policy_action, str) for policy_action in policy["actions"]
        ):
            return deny("malformed policy actions")
        if action not in policy["actions"]:
            return deny("action not defined by policy")

        classification = resource["classification"]
        if classification not in ("normal", "confidential"):
            return deny("unknown classification")

        required_permissions = policy["required_permissions"]
        if not isinstance(required_permissions, dict):
            return deny("malformed required permissions")
        if classification not in required_permissions:
            return deny("missing required permission")
        required_permission = required_permissions[classification]
        if not isinstance(required_permission, str):
            return deny("malformed required permission")
        if required_permission not in user["permissions"]:
            return deny("required permission missing")

        rules = policy["rules"]
        if not isinstance(rules, list):
            return deny("malformed policy rules")

        matching_allow = False

        for rule in rules:
            if not isinstance(rule, dict):
                return deny("malformed policy rule")
            if "effect" not in rule or rule["effect"] not in ("allow", "deny"):
                return deny("malformed policy rule")

            allowed_keys = {"effect", "role", "action", "classification"}
            if any(key not in allowed_keys for key in rule):
                return deny("malformed policy rule")

            if "role" in rule and rule["role"] not in (
                "user", "manager", "administrator"
            ):
                return deny("malformed policy rule")
            if "action" in rule and (
                not isinstance(rule["action"], str)
                or rule["action"] not in policy["actions"]
            ):
                return deny("malformed policy rule")
            if "classification" in rule and rule["classification"] not in (
                "normal", "confidential"
            ):
                return deny("malformed policy rule")

            matches = all(
                (
                    key == "effect"
                    or rule[key]
                    == {
                        "role": user["role"],
                        "action": action,
                        "classification": classification,
                    }[key]
                )
                for key in rule
            )

            if matches:
                if rule["effect"] == "deny":
                    return deny("explicit deny rule matched")
                matching_allow = True

        if matching_allow:
            return {"allowed": True, "reasons": ["explicit allow rule matched"]}

        if user["role"] == "administrator":
            return {"allowed": True, "reasons": ["administrator access"]}
        if user["role"] == "manager" and user["department"] == resource["department"]:
            return {"allowed": True, "reasons": ["manager owns department resource"]}
        if user["role"] == "user" and user["id"] == resource["owner_id"]:
            return {"allowed": True, "reasons": ["user owns resource"]}

        return deny("built-in access rules denied access")
    except Exception:
        return deny("malformed input")