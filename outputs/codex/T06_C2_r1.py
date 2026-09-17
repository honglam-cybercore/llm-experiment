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

        role = user["role"]
        status = user["status"]
        classification = resource["classification"]

        if status not in ("active", "inactive"):
            return deny("unknown account status")
        if status == "inactive":
            return deny("inactive account")
        if role not in ("user", "manager", "administrator"):
            return deny("unknown role")
        if classification not in ("normal", "confidential"):
            return deny("unknown classification")
        if not isinstance(action, str):
            return deny("unknown action")
        if not isinstance(user["permissions"], list) or any(
            not isinstance(permission, str) for permission in user["permissions"]
        ):
            return deny("malformed permissions")

        actions = policy["actions"]
        if not isinstance(actions, list) or any(
            not isinstance(policy_action, str) for policy_action in actions
        ):
            return deny("malformed policy actions")
        if action not in actions:
            return deny("action not defined by policy")

        required_permissions = policy["required_permissions"]
        if not isinstance(required_permissions, dict):
            return deny("malformed required permissions")
        for key, permission in required_permissions.items():
            if key not in ("normal", "confidential") or not isinstance(permission, str):
                return deny("malformed required permissions")

        if classification == "confidential" and classification not in required_permissions:
            return deny("missing confidential permission requirement")

        required_permission = required_permissions.get(classification)
        if required_permission is not None:
            if required_permission not in user["permissions"]:
                return deny("required permission missing")

        rules = policy["rules"]
        if not isinstance(rules, list):
            return deny("malformed policy rules")

        matching_denies = []
        matching_allows = []

        for rule in rules:
            if not isinstance(rule, dict) or "effect" not in rule:
                return deny("malformed policy rule")
            if rule["effect"] not in ("allow", "deny"):
                return deny("malformed policy rule")

            allowed_keys = {"effect", "role", "action", "classification"}
            if any(key not in allowed_keys for key in rule):
                return deny("malformed policy rule")

            if "role" in rule and rule["role"] not in (
                "user",
                "manager",
                "administrator",
            ):
                return deny("malformed policy rule")
            if "action" in rule and not isinstance(rule["action"], str):
                return deny("malformed policy rule")
            if "classification" in rule and rule["classification"] not in (
                "normal",
                "confidential",
            ):
                return deny("malformed policy rule")

            matches = True
            if "role" in rule and rule["role"] != role:
                matches = False
            if "action" in rule and rule["action"] != action:
                matches = False
            if "classification" in rule and rule["classification"] != classification:
                matches = False

            if matches:
                if rule["effect"] == "deny":
                    matching_denies.append(rule)
                else:
                    matching_allows.append(rule)

        if matching_denies:
            return deny("explicit deny rule")

        if matching_allows:
            return {"allowed": True, "reasons": ["explicit allow rule"]}

        if role == "administrator":
            return {"allowed": True, "reasons": ["administrator access"]}
        if role == "manager" and user["department"] == resource["department"]:
            return {"allowed": True, "reasons": ["department manager access"]}
        if role == "user" and user["id"] == resource["owner_id"]:
            return {"allowed": True, "reasons": ["resource ownership"]}

        return deny("built-in access rule denied")

    except Exception:
        return {"allowed": False, "reasons": ["malformed input"]}