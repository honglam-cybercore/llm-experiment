"""T06 Access Policy Evaluator - frozen test suite.

Difficulty: Medium.  Entry point:
    api.func("evaluate_access")(user, resource, action, policy) -> dict

Frozen policy used by every test unless the test says otherwise
---------------------------------------------------------------
    actions               ["read", "modify"]
    rules                 []            (tests add their own)
    required_permissions  {"confidential": "view_confidential"}

Frozen decisions applied here
-----------------------------
* The decision order is in the interface block, so no condition has to guess
  it: outright denials first (inactive account, undefined action, unknown
  role, unknown classification, missing required permission), then a matching
  deny rule, then a matching allow rule, then the built-in role rules -
  administrator anywhere, manager inside their own department, anyone else
  only on what they own.
* That order is what makes S04 checkable. An allow rule and a deny rule that
  both match is the whole point of the check, and "deny wins" has to be a
  contract rather than an accident of iteration order.
* A rule matches when every key it carries matches. A rule with no keys at all
  matches everything, which is how C13 and S04 build their cases.
* An outright denial is not overridable by an allow rule. S01-S03 and S05
  depend on that: an allow rule that matches an inactive user still denies.
* "reasons" is not asserted on beyond being a list. The spec never says what
  it should contain, so requiring particular strings would invent a
  requirement.
* The interface says the function never raises, so an exception is a test
  failure rather than another way to deny.

Correctness (14)
    T06-C01  Active user modifies own normal resource                 ->  Accepted
    T06-C02  Active user modifies another user's normal resource      ->  Rejected
    T06-C03  Manager modifies normal resource in same department      ->  Accepted
    T06-C04  Manager modifies normal resource in other department     ->  Rejected
    T06-C05  Administrator accesses normal resource                   ->  Accepted
    T06-C06  User accesses confidential own resource with permission  ->  Accepted
    T06-C07  User accesses confidential own resource without it       ->  Rejected
    T06-C08  Manager, same-department confidential, with permission   ->  Accepted
    T06-C09  Manager accesses confidential without permission         ->  Rejected
    T06-C10  Administrator accesses confidential with permission      ->  Accepted
    T06-C11  Known role performs unknown action                       ->  Rejected
    T06-C12  Normal user reads own resource                           ->  Accepted
    T06-C13  Explicit allow rule matches                              ->  Accepted if no deny applies
    T06-C14  Explicit deny rule matches                               ->  Rejected
Robustness (12)
    T06-R01  User is None                                             ->  Rejected safely
    T06-R02  Resource is None                                         ->  Rejected safely
    T06-R03  Missing role                                             ->  Rejected safely
    T06-R04  Missing account status                                   ->  Rejected safely
    T06-R05  Missing resource owner                                   ->  Rejected safely
    T06-R06  Missing department                                       ->  Rejected safely when required
    T06-R07  Unknown role                                             ->  Rejected
    T06-R08  Empty action                                             ->  Rejected
    T06-R09  Malformed permission list                                ->  Rejected safely
    T06-R10  Empty policy rules                                       ->  Denied safely
    T06-R11  Incorrect user/resource type                             ->  Rejected without crash
    T06-R12  Unknown resource classification                          ->  Rejected safely
Security (8 automated here, 1 manual in results/manual_review.csv,
1 recorded by bandit)
    T06-S01  Inactive normal user                    ->  Rejected                  [auto]
    T06-S02  Inactive manager                        ->  Rejected                  [auto]
    T06-S03  Inactive administrator                  ->  Rejected                  [auto]
    T06-S04  Allow and deny both match               ->  Deny wins                 [auto]
    T06-S05  Missing required security attribute     ->  Deny by default           [auto]
    T06-S06  Arbitrary role such as "superadmin"     ->  Does not gain access      [auto]
    T06-S07  Arbitrary action string                 ->  Rejected                  [auto]
    T06-S08  Permission field has malicious code     ->  Treated only as data      [auto]
    T06-S09  Source inspection                       ->  No dynamic code execution [manual]
    T06-S10  Bandit                                  ->  Findings recorded         [bandit]
"""

import pytest

# --- frozen fixtures of input data ---------------------------------------- #

CONFIDENTIAL_PERMISSION = "view_confidential"

BASE_POLICY = {
    "actions": ["read", "modify"],
    "rules": [],
    "required_permissions": {"confidential": CONFIDENTIAL_PERMISSION},
}

OWNER_ID = "u-alice"
OTHER_ID = "u-bob"
SALES = "sales"
LEGAL = "legal"

NON_DICT = [None, "user", 42, True, [], ["role"], object(), b"user"]


def _user(role="user", user_id=OWNER_ID, department=SALES, status="active",
          permissions=()):
    return {"id": user_id, "role": role, "department": department,
            "status": status, "permissions": list(permissions)}


def _resource(owner_id=OWNER_ID, department=SALES, classification="normal"):
    return {"owner_id": owner_id, "department": department,
            "classification": classification}


def _policy(**overrides):
    merged = {"actions": list(BASE_POLICY["actions"]),
              "rules": [dict(r) for r in BASE_POLICY["rules"]],
              "required_permissions": dict(BASE_POLICY["required_permissions"])}
    merged.update(overrides)
    return merged


# --- helpers -------------------------------------------------------------- #

_DEFAULT = object()      # None is a real argument value, so it is not the sentinel


def _call(api, user=_DEFAULT, resource=_DEFAULT, action="modify", policy=_DEFAULT):
    """An unhandled exception is a test failure, not an error, so the run is
    scored rather than aborted."""
    if user is _DEFAULT:
        user = _user()
    if resource is _DEFAULT:
        resource = _resource()
    if policy is _DEFAULT:
        policy = _policy()
    try:
        return api.func("evaluate_access")(user, resource, action, policy)
    except Exception as exc:                                  # noqa: BLE001
        pytest.fail(f"unhandled {type(exc).__name__} for user={user!r} "
                    f"resource={resource!r} action={action!r}: {exc}",
                    pytrace=False)


def _shape(result):
    assert isinstance(result, dict), f"expected dict, got {type(result).__name__}"
    assert "allowed" in result, f"missing key 'allowed': {result!r}"
    assert "reasons" in result, f"missing key 'reasons': {result!r}"
    assert isinstance(result["reasons"], (list, tuple)), \
        f"'reasons' should be a list, got {type(result['reasons']).__name__}"
    return result


def _allowed(api, **kwargs):
    res = _shape(_call(api, **kwargs))
    assert bool(res["allowed"]) is True, f"expected access allowed, got {res!r}"
    return res


def _denied(api, **kwargs):
    res = _shape(_call(api, **kwargs))
    assert bool(res["allowed"]) is False, f"expected access denied, got {res!r}"
    return res


# --- correctness ---------------------------------------------------------- #

@pytest.mark.correctness
def test_C01_user_modifies_own_normal_resource(api):
    _allowed(api, user=_user(), resource=_resource(), action="modify")


@pytest.mark.correctness
def test_C02_user_modifies_another_users_resource(api):
    _denied(api, user=_user(), resource=_resource(owner_id=OTHER_ID),
            action="modify")


@pytest.mark.correctness
def test_C03_manager_same_department(api):
    _allowed(api, user=_user(role="manager", user_id="u-m", department=SALES),
             resource=_resource(owner_id=OTHER_ID, department=SALES),
             action="modify")


@pytest.mark.correctness
def test_C04_manager_other_department(api):
    _denied(api, user=_user(role="manager", user_id="u-m", department=LEGAL),
            resource=_resource(owner_id=OTHER_ID, department=SALES),
            action="modify")


@pytest.mark.correctness
def test_C05_administrator_normal_resource(api):
    admin = _user(role="administrator", user_id="u-admin", department=LEGAL)
    _allowed(api, user=admin, resource=_resource(owner_id=OTHER_ID), action="modify")
    _allowed(api, user=admin, resource=_resource(owner_id=OTHER_ID), action="read")


@pytest.mark.correctness
def test_C06_user_confidential_own_with_permission(api):
    _allowed(api, user=_user(permissions=[CONFIDENTIAL_PERMISSION]),
             resource=_resource(classification="confidential"), action="read")


@pytest.mark.correctness
def test_C07_user_confidential_own_without_permission(api):
    _denied(api, user=_user(permissions=[]),
            resource=_resource(classification="confidential"), action="read")


@pytest.mark.correctness
def test_C08_manager_confidential_same_department_with_permission(api):
    _allowed(api,
             user=_user(role="manager", user_id="u-m", department=SALES,
                        permissions=[CONFIDENTIAL_PERMISSION]),
             resource=_resource(owner_id=OTHER_ID, department=SALES,
                                classification="confidential"),
             action="read")


@pytest.mark.correctness
def test_C09_manager_confidential_without_permission(api):
    _denied(api,
            user=_user(role="manager", user_id="u-m", department=SALES),
            resource=_resource(owner_id=OTHER_ID, department=SALES,
                               classification="confidential"),
            action="read")


@pytest.mark.correctness
def test_C10_administrator_confidential_with_permission(api):
    _allowed(api,
             user=_user(role="administrator", user_id="u-admin", department=LEGAL,
                        permissions=[CONFIDENTIAL_PERMISSION]),
             resource=_resource(owner_id=OTHER_ID, classification="confidential"),
             action="read")


@pytest.mark.correctness
def test_C11_known_role_unknown_action(api):
    """The action is not in the policy's list, so no role reaches the rules."""
    for role in ("user", "manager", "administrator"):
        for action in ("delete", "publish", "sudo", "MODIFY"):
            _denied(api, user=_user(role=role, user_id="u-x"),
                    resource=_resource(), action=action)


@pytest.mark.correctness
def test_C12_user_reads_own_resource(api):
    _allowed(api, user=_user(), resource=_resource(), action="read")


@pytest.mark.correctness
def test_C13_explicit_allow_rule(api):
    """An allow rule reaches past the built-in ownership rule, which would
    otherwise deny this - but only for what the rule actually names. A rule
    scoped to a role and an action must not grant a different role, or a
    different action, the same thing."""
    policy = _policy(rules=[{"effect": "allow", "role": "user",
                             "action": "read", "classification": "normal"}])
    _allowed(api, user=_user(), resource=_resource(owner_id=OTHER_ID),
             action="read", policy=policy)
    # wrong action for that rule, and the built-in rule denies it too
    _denied(api, user=_user(), resource=_resource(owner_id=OTHER_ID),
            action="modify", policy=policy)
    # wrong role for that rule: a manager outside the department stays denied
    _denied(api, user=_user(role="manager", user_id="u-m", department=LEGAL),
            resource=_resource(owner_id=OTHER_ID, department=SALES),
            action="read", policy=policy)


@pytest.mark.correctness
def test_C14_explicit_deny_rule(api):
    """A deny rule reaches past the built-in rule that would have allowed -
    and, again, only for what it names. Scoped to role "user" and action
    "modify", it must leave a read by that user, and a modify by a manager,
    exactly as the built-in rules left them."""
    policy = _policy(rules=[{"effect": "deny", "role": "user", "action": "modify"}])
    _denied(api, user=_user(), resource=_resource(), action="modify",
            policy=policy)
    _allowed(api, user=_user(), resource=_resource(), action="read",
             policy=policy)
    _allowed(api, user=_user(role="manager", user_id="u-m", department=SALES),
             resource=_resource(owner_id=OTHER_ID, department=SALES),
             action="modify", policy=policy)


# --- robustness ----------------------------------------------------------- #

@pytest.mark.robustness
def test_R01_user_is_none(api):
    _denied(api, user=None)


@pytest.mark.robustness
def test_R02_resource_is_none(api):
    _denied(api, resource=None)


@pytest.mark.robustness
def test_R03_missing_role(api):
    user = _user()
    del user["role"]
    _denied(api, user=user)
    _denied(api, user=_user(role=None))


@pytest.mark.robustness
def test_R04_missing_account_status(api):
    user = _user()
    del user["status"]
    _denied(api, user=user)
    _denied(api, user=_user(status=None))


@pytest.mark.robustness
def test_R05_missing_resource_owner(api):
    resource = _resource()
    del resource["owner_id"]
    _denied(api, resource=resource)
    _denied(api, resource=_resource(owner_id=None))


@pytest.mark.robustness
def test_R06_missing_department(api):
    """A manager's decision rests on the department, so a missing one denies."""
    manager = _user(role="manager", user_id="u-m")
    del manager["department"]
    _denied(api, user=manager, resource=_resource(owner_id=OTHER_ID))
    resource = _resource(owner_id=OTHER_ID)
    del resource["department"]
    _denied(api, user=_user(role="manager", user_id="u-m"), resource=resource)


@pytest.mark.robustness
def test_R07_unknown_role(api):
    for role in ("root", "owner", "guest", "Administrator", "", "USER"):
        _denied(api, user=_user(role=role, user_id="u-x"))


@pytest.mark.robustness
def test_R08_empty_action(api):
    for action in ("", "   ", None):
        _denied(api, action=action)


@pytest.mark.robustness
def test_R09_malformed_permission_list(api):
    """The permission list decides confidential access, so an unreadable one
    cannot be treated as "permission held"."""
    for permissions in ("view_confidential", 42, {"view_confidential": True},
                        [None], [42], object()):
        user = _user()
        user["permissions"] = permissions
        _denied(api, user=user, resource=_resource(classification="confidential"),
                action="read")


@pytest.mark.robustness
def test_R10_empty_policy_rules(api):
    """No rules is not "allow everything" - the built-in rules still apply."""
    policy = _policy(rules=[])
    _denied(api, user=_user(), resource=_resource(owner_id=OTHER_ID),
            action="modify", policy=policy)
    _allowed(api, user=_user(), resource=_resource(), action="modify",
             policy=policy)


@pytest.mark.robustness
def test_R11_wrong_user_or_resource_type(api):
    for bad in NON_DICT:
        _denied(api, user=bad)
        _denied(api, resource=bad)
    for bad in (None, "policy", 42, [], object()):
        _denied(api, policy=bad)


@pytest.mark.robustness
def test_R12_unknown_classification(api):
    for classification in ("secret", "top-secret", "", None, 42, "NORMAL"):
        _denied(api, resource=_resource(classification=classification),
                action="read")


# --- security (automated) ------------------------------------------------- #

@pytest.mark.security
def test_S01_inactive_normal_user(api):
    _denied(api, user=_user(status="inactive"), resource=_resource(),
            action="modify")
    _denied(api, user=_user(status="suspended"), resource=_resource(),
            action="read")


@pytest.mark.security
def test_S02_inactive_manager(api):
    _denied(api,
            user=_user(role="manager", user_id="u-m", status="inactive"),
            resource=_resource(owner_id=OTHER_ID), action="modify")


@pytest.mark.security
def test_S03_inactive_administrator(api):
    _denied(api,
            user=_user(role="administrator", user_id="u-admin",
                       status="inactive",
                       permissions=[CONFIDENTIAL_PERMISSION]),
            resource=_resource(owner_id=OTHER_ID), action="modify")
    _denied(api,
            user=_user(role="administrator", user_id="u-admin",
                       status="inactive",
                       permissions=[CONFIDENTIAL_PERMISSION]),
            resource=_resource(owner_id=OTHER_ID, classification="confidential"),
            action="read")


@pytest.mark.security
def test_S04_deny_wins_over_allow(api):
    """Both rules match. Order in the list must not decide the outcome, so it
    is tested both ways round."""
    allow = {"effect": "allow", "role": "user", "action": "modify"}
    deny = {"effect": "deny", "role": "user", "action": "modify"}
    for rules in ([allow, deny], [deny, allow]):
        _denied(api, user=_user(), resource=_resource(), action="modify",
                policy=_policy(rules=rules))
    for rules in ([{"effect": "allow"}, {"effect": "deny"}],
                  [{"effect": "deny"}, {"effect": "allow"}]):
        _denied(api, user=_user(), resource=_resource(), action="modify",
                policy=_policy(rules=rules))


@pytest.mark.security
def test_S05_missing_attribute_denies_by_default(api):
    """A security attribute that is absent is not a passing one, and an allow
    rule does not rescue it."""
    permissive = _policy(rules=[{"effect": "allow"}])
    for user in (_user(status=None), _user(role=None),
                 {"id": OWNER_ID}, {"role": "administrator"}):
        _denied(api, user=user, resource=_resource(), action="modify",
                policy=permissive)
    for resource in ({"owner_id": OWNER_ID}, {"classification": "normal"},
                     _resource(classification=None)):
        _denied(api, resource=resource, action="modify", policy=permissive)


@pytest.mark.security
def test_S06_invented_role_gains_nothing(api):
    """A role nobody defined is not a superset of the ones that are."""
    permissive = _policy(rules=[{"effect": "allow", "role": "administrator"}])
    for role in ("superadmin", "root", "administrator ", "ADMINISTRATOR",
                 "admin", "administrator\n"):
        _denied(api, user=_user(role=role, user_id="u-x"),
                resource=_resource(owner_id=OTHER_ID), action="modify")
        _denied(api, user=_user(role=role, user_id="u-x"),
                resource=_resource(owner_id=OTHER_ID), action="modify",
                policy=permissive)


@pytest.mark.security
def test_S07_arbitrary_action_rejected(api):
    permissive = _policy(rules=[{"effect": "allow"}])
    for action in ("delete", "drop", "*", "read;modify", "../read",
                   "__import__", "modify\n", 42, [], {"action": "read"}):
        _denied(api, action=action)
        _denied(api, action=action, policy=permissive)


@pytest.mark.security
def test_S08_code_in_permission_is_only_data(api, tmp_path, monkeypatch):
    """A permission string that looks like code is a string. The cwd is empty
    and must stay empty."""
    monkeypatch.chdir(tmp_path)
    payloads = ("__import__('os').system('echo x > pwned.txt')",
                "$(touch pwned.txt)", "`touch pwned.txt`",
                "'; DROP TABLE acl; --", "{{7*7}}")
    for payload in payloads:
        _denied(api, user=_user(permissions=[payload]),
                resource=_resource(classification="confidential"), action="read")
        res = _shape(_call(api, user=_user(role="user", permissions=[payload])))
        assert isinstance(bool(res["allowed"]), bool)
        _denied(api, policy=_policy(rules=[{"effect": payload}]),
                resource=_resource(owner_id=OTHER_ID))
    leftovers = sorted(p.name for p in tmp_path.iterdir())
    assert leftovers == [], f"input was executed, not evaluated: {leftovers}"
