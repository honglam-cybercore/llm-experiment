def evaluate_access(user, resource, action, policy) -> dict:
    def deny(reason):
        return {"allowed": False, "reasons": [reason]}

    try:
        if not isinstance(user, dict) or not isinstance(resource, dict) or not isinstance(policy, dict):
            return deny("malformed input")

        required_user = {"id", "role", "department", "status", "permissions"}
        required_resource = {"owner_id", "department", "classification"}
        required_policy = {"actions", "rules", "required_permissions"}

        if not required_user.issubset(user):
            return deny("missing user information")
        if not required_resource.issubset(resource):
            return deny("missing resource information")
        if not required_policy.issubset(policy):
            return deny("missing policy information")

        user_id = user["id"]
        role = user["role"]
        user_department = user["department"]
        status = user["status"]
        permissions = user["permissions"]

        owner_id = resource["owner_id"]
        resource_department = resource["department"]
        classification = resource["classification"]

        if not all(isinstance(value, str) and value for value in (
            user_id, role, user_department, status,
            owner_id, resource_department, classification, action
        )):
            return deny("malformed input")

        if status == "inactive":
            return deny("inactive account")
        if status != "active":
            return deny("unknown account status")

        if role not in {"user", "manager", "administrator"}:
            return deny("unknown role")

        if classification not in {"normal", "confidential"}:
            return deny("unknown classification")

        if not isinstance(permissions, list) or not all(
            isinstance(permission, str) and permission for permission in permissions
        ):
            return deny("malformed permissions")

        actions = policy["actions"]
        if not isinstance(actions, list) or not all(
            isinstance(policy_action, str) and policy_action for policy_action in actions
        ):
            return deny("malformed policy actions")
        if action not in actions:
            return deny("action not defined by policy")

        required_permissions = policy["required_permissions"]
        if not isinstance(required_permissions, dict):
            return deny("malformed required permissions")

        for permission_classification, permission in required_permissions.items():
            if permission_classification not in {"normal", "confidential"}:
                return deny("unknown required-permission classification")
            if not isinstance(permission, str) or not permission:
                return deny("malformed required permission")

        required_permission = required_permissions.get(classification)
        if required_permission is not None and required_permission not in permissions:
            return deny("required permission missing")

        rules = policy["rules"]
        if not isinstance(rules, list):
            return deny("malformed policy rules")

        allowed_rule_keys = {"effect", "role", "action", "classification"}
        normalized_rules = []

        for rule in rules:
            if not isinstance(rule, dict):
                return deny("malformed policy rule")
            if "effect" not in rule or rule["effect"] not in {"allow", "deny"}:
                return deny("malformed policy rule")
            if any(key not in allowed_rule_keys for key in rule):
                return deny("malformed policy rule")

            if "role" in rule and rule["role"] not in {
                "user", "manager", "administrator"
            }:
                return deny("unknown rule role")

            if "action" in rule and (
                not isinstance(rule["action"], str) or rule["action"] not in actions
            ):
                return deny("unknown rule action")

            if "classification" in rule and rule["classification"] not in {
                "normal", "confidential"
            }:
                return deny("unknown rule classification")

            normalized_rules.append(rule)

        def matches(rule):
            return (
                ("role" not in rule or rule["role"] == role)
                and ("action" not in rule or rule["action"] == action)
                and (
                    "classification" not in rule
                    or rule["classification"] == classification
                )
            )

        if any(rule["effect"] == "deny" and matches(rule) for rule in normalized_rules):
            return deny("explicit deny rule")

        if any(rule["effect"] == "allow" and matches(rule) for rule in normalized_rules):
            return {"allowed": True, "reasons": ["explicit allow rule"]}

        if role == "administrator":
            return {"allowed": True, "reasons": ["administrator access"]}
        if role == "manager" and user_department == resource_department:
            return {"allowed": True, "reasons": ["department manager access"]}
        if role == "user" and user_id == owner_id:
            return {"allowed": True, "reasons": ["resource ownership"]}

        return deny("built-in access rule denied")
    except Exception:
        return deny("malformed input")