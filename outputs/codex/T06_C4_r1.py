def evaluate_access(user, resource, action, policy) -> dict:
    def denied(reason):
        return {"allowed": False, "reasons": [reason]}

    try:
        if not isinstance(user, dict) or not isinstance(resource, dict):
            return denied("malformed input")
        if not isinstance(policy, dict) or not isinstance(action, str):
            return denied("malformed input")

        required_user = {"id", "role", "department", "status", "permissions"}
        required_resource = {"owner_id", "department", "classification"}
        required_policy = {"actions", "rules", "required_permissions"}

        if set(user) != required_user or set(resource) != required_resource:
            return denied("missing or malformed information")
        if set(policy) != required_policy:
            return denied("missing or malformed policy information")

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

        if (
            not isinstance(user_id, str)
            or not user_id
            or not isinstance(owner_id, str)
            or not owner_id
            or not isinstance(user_department, str)
            or not user_department
            or not isinstance(resource_department, str)
            or not resource_department
            or not isinstance(role, str)
            or not isinstance(status, str)
            or not isinstance(permissions, list)
            or not all(isinstance(permission, str) for permission in permissions)
            or not isinstance(actions, list)
            or not all(isinstance(item, str) and item for item in actions)
            or not isinstance(rules, list)
            or not isinstance(required_permissions, dict)
        ):
            return denied("missing or malformed information")

        valid_roles = {"user", "manager", "administrator"}
        valid_statuses = {"active", "inactive"}
        valid_classifications = {"normal", "confidential"}

        if status not in valid_statuses:
            return denied("unknown account status")
        if status == "inactive":
            return denied("inactive account")
        if role not in valid_roles:
            return denied("unknown role")
        if classification not in valid_classifications:
            return denied("unknown classification")
        if action not in actions:
            return denied("action is not defined by policy")

        if (
            set(required_permissions) != valid_classifications
            or not all(
                isinstance(permission, str) and permission
                for permission in required_permissions.values()
            )
        ):
            return denied("missing or malformed permission policy")

        required_permission = required_permissions[classification]
        if required_permission not in permissions:
            return denied("required permission missing")

        valid_rule_keys = {"effect", "role", "action", "classification"}
        normalized_rules = []

        for rule in rules:
            if not isinstance(rule, dict):
                return denied("malformed policy rule")
            if not set(rule).issubset(valid_rule_keys):
                return denied("malformed policy rule")
            if rule.get("effect") not in {"allow", "deny"}:
                return denied("malformed policy rule")

            if "role" in rule and rule["role"] not in valid_roles:
                return denied("malformed policy rule")
            if "action" in rule:
                if (
                    not isinstance(rule["action"], str)
                    or rule["action"] not in actions
                ):
                    return denied("malformed policy rule")
            if "classification" in rule:
                if rule["classification"] not in valid_classifications:
                    return denied("malformed policy rule")

            normalized_rules.append(rule)

        def matches(rule):
            return all(
                (
                    key == "effect"
                    or (
                        key == "role"
                        and rule[key] == role
                    )
                    or (
                        key == "action"
                        and rule[key] == action
                    )
                    or (
                        key == "classification"
                        and rule[key] == classification
                    )
                )
                for key in rule
            )

        for rule in normalized_rules:
            if rule["effect"] == "deny" and matches(rule):
                return denied("explicit deny rule matched")

        for rule in normalized_rules:
            if rule["effect"] == "allow" and matches(rule):
                return {"allowed": True, "reasons": ["explicit allow rule matched"]}

        if role == "administrator":
            return {"allowed": True, "reasons": ["administrator access"]}
        if role == "manager" and user_department == resource_department:
            return {"allowed": True, "reasons": ["department manager access"]}
        if role == "user" and user_id == owner_id:
            return {"allowed": True, "reasons": ["resource ownership"]}

        return denied("built-in access rule denied")

    except Exception:
        return {"allowed": False, "reasons": ["malformed input"]}