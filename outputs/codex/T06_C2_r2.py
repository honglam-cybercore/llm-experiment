def evaluate_access(user, resource, action, policy) -> dict:
    try:
        if not isinstance(user, dict) or not isinstance(resource, dict) or not isinstance(policy, dict):
            return {"allowed": False, "reasons": ["malformed input"]}

        user_required = {"id", "role", "department", "status", "permissions"}
        resource_required = {"owner_id", "department", "classification"}
        policy_required = {"actions", "rules", "required_permissions"}

        if not user_required.issubset(user) or not resource_required.issubset(resource):
            return {"allowed": False, "reasons": ["missing required information"]}
        if not policy_required.issubset(policy):
            return {"allowed": False, "reasons": ["missing required information"]}

        role = user["role"]
        status = user["status"]
        classification = resource["classification"]

        if status not in ("active", "inactive"):
            return {"allowed": False, "reasons": ["unknown account status"]}
        if status == "inactive":
            return {"allowed": False, "reasons": ["inactive account"]}

        if role not in ("user", "manager", "administrator"):
            return {"allowed": False, "reasons": ["unknown role"]}

        if not isinstance(action, str):
            return {"allowed": False, "reasons": ["unknown action"]}
        if not isinstance(policy["actions"], list) or any(
            not isinstance(item, str) for item in policy["actions"]
        ):
            return {"allowed": False, "reasons": ["malformed policy"]}
        if action not in policy["actions"]:
            return {"allowed": False, "reasons": ["action not defined by policy"]}

        if classification not in ("normal", "confidential"):
            return {"allowed": False, "reasons": ["unknown classification"]}

        if not isinstance(user["permissions"], list) or any(
            not isinstance(permission, str) for permission in user["permissions"]
        ):
            return {"allowed": False, "reasons": ["malformed user"]}

        required_permissions = policy["required_permissions"]
        if not isinstance(required_permissions, dict):
            return {"allowed": False, "reasons": ["malformed policy"]}

        if classification == "confidential" and classification not in required_permissions:
            return {"allowed": False, "reasons": ["missing required permission"]}

        if classification in required_permissions:
            permission = required_permissions[classification]
            if not isinstance(permission, str):
                return {"allowed": False, "reasons": ["malformed policy"]}
            if permission not in user["permissions"]:
                return {"allowed": False, "reasons": ["missing required permission"]}

        rules = policy["rules"]
        if not isinstance(rules, list):
            return {"allowed": False, "reasons": ["malformed policy"]}

        matching_denies = []
        matching_allows = []

        for rule in rules:
            if not isinstance(rule, dict) or "effect" not in rule:
                return {"allowed": False, "reasons": ["malformed policy"]}

            allowed_keys = {"effect", "role", "action", "classification"}
            if any(key not in allowed_keys for key in rule):
                return {"allowed": False, "reasons": ["malformed policy"]}
            if rule["effect"] not in ("allow", "deny"):
                return {"allowed": False, "reasons": ["malformed policy"]}

            if "role" in rule and not isinstance(rule["role"], str):
                return {"allowed": False, "reasons": ["malformed policy"]}
            if "action" in rule and not isinstance(rule["action"], str):
                return {"allowed": False, "reasons": ["malformed policy"]}
            if "classification" in rule and rule["classification"] not in (
                "normal",
                "confidential",
            ):
                return {"allowed": False, "reasons": ["malformed policy"]}

            matches = True
            for key, value in rule.items():
                if key != "effect":
                    actual = role if key == "role" else action if key == "action" else classification
                    if actual != value:
                        matches = False
                        break

            if matches:
                if rule["effect"] == "deny":
                    matching_denies.append(rule)
                else:
                    matching_allows.append(rule)

        if matching_denies:
            return {"allowed": False, "reasons": ["explicit deny rule"]}

        if matching_allows:
            return {"allowed": True, "reasons": ["explicit allow rule"]}

        if role == "administrator":
            allowed = True
        elif role == "manager":
            allowed = user["department"] == resource["department"]
        else:
            allowed = user["id"] == resource["owner_id"]

        return {
            "allowed": allowed,
            "reasons": ["built-in rule allows"] if allowed else ["built-in rule denies"],
        }

    except Exception:
        return {"allowed": False, "reasons": ["malformed input"]}