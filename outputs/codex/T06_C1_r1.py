def evaluate_access(user, resource, action, policy) -> dict:
    result = {"allowed": False, "reasons": []}

    try:
        if type(user) is not dict or type(resource) is not dict or type(policy) is not dict:
            result["reasons"].append("malformed input")
            return result

        required_user = ("id", "role", "department", "status", "permissions")
        required_resource = ("owner_id", "department", "classification")
        required_policy = ("actions", "rules", "required_permissions")

        if any(key not in user for key in required_user):
            result["reasons"].append("missing user data")
            return result
        if any(key not in resource for key in required_resource):
            result["reasons"].append("missing resource data")
            return result
        if any(key not in policy for key in required_policy):
            result["reasons"].append("missing policy data")
            return result

        role = user["role"]
        status = user["status"]
        classification = resource["classification"]

        if type(role) is not str or role not in {"user", "manager", "administrator"}:
            result["reasons"].append("unknown role")
            return result
        if type(status) is not str or status not in {"active", "inactive"}:
            result["reasons"].append("unknown account status")
            return result
        if status == "inactive":
            result["reasons"].append("inactive account")
            return result
        if type(action) is not str:
            result["reasons"].append("malformed action")
            return result
        if type(classification) is not str or classification not in {"normal", "confidential"}:
            result["reasons"].append("unknown classification")
            return result
        if type(user["permissions"]) is not list or any(
            type(permission) is not str for permission in user["permissions"]
        ):
            result["reasons"].append("malformed permissions")
            return result
        if type(policy["actions"]) is not list or any(
            type(policy_action) is not str for policy_action in policy["actions"]
        ):
            result["reasons"].append("malformed policy actions")
            return result
        if action not in policy["actions"]:
            result["reasons"].append("action not defined by policy")
            return result

        required_permissions = policy["required_permissions"]
        if type(required_permissions) is not dict:
            result["reasons"].append("malformed required permissions")
            return result
        if classification not in required_permissions:
            result["reasons"].append("missing required permission")
            return result

        required_permission = required_permissions[classification]
        if type(required_permission) is not str:
            result["reasons"].append("malformed required permission")
            return result
        if required_permission not in user["permissions"]:
            result["reasons"].append("required permission missing")
            return result

        rules = policy["rules"]
        if type(rules) is not list:
            result["reasons"].append("malformed policy rules")
            return result

        deny_match = False
        allow_match = False

        for rule in rules:
            if type(rule) is not dict or "effect" not in rule:
                result["reasons"].append("malformed policy rule")
                return result

            if any(key not in {"effect", "role", "action", "classification"} for key in rule):
                result["reasons"].append("malformed policy rule")
                return result

            effect = rule["effect"]
            if type(effect) is not str or effect not in {"allow", "deny"}:
                result["reasons"].append("malformed policy rule")
                return result

            if "role" in rule and (
                type(rule["role"]) is not str
                or rule["role"] not in {"user", "manager", "administrator"}
            ):
                result["reasons"].append("malformed policy rule")
                return result
            if "action" in rule and type(rule["action"]) is not str:
                result["reasons"].append("malformed policy rule")
                return result
            if "classification" in rule and (
                type(rule["classification"]) is not str
                or rule["classification"] not in {"normal", "confidential"}
            ):
                result["reasons"].append("malformed policy rule")
                return result

            matches = (
                ("role" not in rule or rule["role"] == role)
                and ("action" not in rule or rule["action"] == action)
                and (
                    "classification" not in rule
                    or rule["classification"] == classification
                )
            )

            if matches:
                if effect == "deny":
                    deny_match = True
                else:
                    allow_match = True

        if deny_match:
            result["reasons"].append("denied by policy rule")
            return result
        if allow_match:
            result["allowed"] = True
            result["reasons"].append("allowed by policy rule")
            return result

        try:
            owns_resource = user["id"] == resource["owner_id"]
            same_department = user["department"] == resource["department"]
        except BaseException:
            result["reasons"].append("malformed ownership or department data")
            return result

        if role == "administrator":
            result["allowed"] = True
            result["reasons"].append("administrator access")
        elif role == "manager" and same_department:
            result["allowed"] = True
            result["reasons"].append("manager access within department")
        elif role == "user" and owns_resource:
            result["allowed"] = True
            result["reasons"].append("resource ownership")
        else:
            result["reasons"].append("built-in access rule denied")

        return result
    except BaseException:
        return {"allowed": False, "reasons": ["malformed input"]}