def evaluate_access(user, resource, action, policy) -> dict:
    def deny(reason):
        return {"allowed": False, "reasons": [reason]}

    try:
        if type(user) is not dict or type(resource) is not dict or type(policy) is not dict:
            return deny("malformed input")

        required_user = {"id", "role", "department", "status", "permissions"}
        required_resource = {"owner_id", "department", "classification"}
        required_policy = {"actions", "rules", "required_permissions"}

        if not required_user.issubset(user):
            return deny("malformed input")
        if not required_resource.issubset(resource):
            return deny("malformed input")
        if not required_policy.issubset(policy):
            return deny("malformed input")

        role = user["role"]
        status = user["status"]
        classification = resource["classification"]

        if type(role) is not str or role not in {"user", "manager", "administrator"}:
            return deny("unknown role")
        if type(status) is not str or status not in {"active", "inactive"}:
            return deny("malformed input")
        if status == "inactive":
            return deny("inactive account")

        if type(action) is not str or not action:
            return deny("malformed input")

        actions = policy["actions"]
        if type(actions) is not list or any(type(item) is not str or not item for item in actions):
            return deny("malformed input")
        if action not in actions:
            return deny("action not defined by policy")

        if type(classification) is not str or classification not in {"normal", "confidential"}:
            return deny("unknown resource classification")

        permissions = user["permissions"]
        if type(permissions) is not list or any(type(item) is not str for item in permissions):
            return deny("malformed input")

        required_permissions = policy["required_permissions"]
        if type(required_permissions) is not dict:
            return deny("malformed input")
        for key, permission in required_permissions.items():
            if (
                type(key) is not str
                or key not in {"normal", "confidential"}
                or type(permission) is not str
                or not permission
            ):
                return deny("malformed input")

        required_permission = required_permissions.get(classification)
        if required_permission is not None and required_permission not in permissions:
            return deny("required permission missing")

        rules = policy["rules"]
        if type(rules) is not list:
            return deny("malformed input")

        allowed_rule = False
        for rule in rules:
            if type(rule) is not dict or "effect" not in rule:
                return deny("malformed input")

            if any(key not in {"effect", "role", "action", "classification"} for key in rule):
                return deny("malformed input")

            effect = rule["effect"]
            if type(effect) is not str or effect not in {"allow", "deny"}:
                return deny("malformed input")

            if "role" in rule and (
                type(rule["role"]) is not str
                or rule["role"] not in {"user", "manager", "administrator"}
            ):
                return deny("malformed input")
            if "action" in rule and (
                type(rule["action"]) is not str
                or rule["action"] not in actions
            ):
                return deny("malformed input")
            if "classification" in rule and (
                type(rule["classification"]) is not str
                or rule["classification"] not in {"normal", "confidential"}
            ):
                return deny("malformed input")

            matches = True
            if "role" in rule and rule["role"] != role:
                matches = False
            if "action" in rule and rule["action"] != action:
                matches = False
            if "classification" in rule and rule["classification"] != classification:
                matches = False

            if matches:
                if effect == "deny":
                    return deny("denied by policy rule")
                allowed_rule = True

        if allowed_rule:
            return {"allowed": True, "reasons": ["allowed by policy rule"]}

        if role == "administrator":
            return {"allowed": True, "reasons": ["administrator access"]}
        if role == "manager" and user["department"] == resource["department"]:
            return {"allowed": True, "reasons": ["same-department manager access"]}
        if role == "user" and user["id"] == resource["owner_id"]:
            return {"allowed": True, "reasons": ["resource owner access"]}

        return deny("built-in access rule denied")

    except Exception:
        return deny("malformed input")