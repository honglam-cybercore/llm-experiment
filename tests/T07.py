"""T07 Configuration Merge Engine - frozen test suite.

Difficulty: Medium.  Entry point:
    api.func("merge_config")(defaults, file_config, env_config, cli_config, schema) -> dict

Frozen schema used by every test unless the test says otherwise
---------------------------------------------------------------
    name           str,  required
    server.port    int,  required, min 1, max 65535
    server.debug   bool, optional
    timeout        int,  optional, min 0
    secret         str,  optional

Precedence, lowest to highest: defaults, file, environment, command line.

Frozen decisions applied here
-----------------------------
* The failure mode is an exception. The interface says merge_config returns the
  merged configuration and raises ValueError for anything it cannot accept, so
  returning a partial dict is a failure of the robustness tests rather than a
  lenient pass. Every rejection below asserts on ValueError specifically.
* A nested key is written in the schema as a dotted path ("server.port") and in
  the sources as a nested dict ({"server": {"port": 8080}}). C06 and C07 are
  what make the difference between merging dicts key by key and replacing the
  whole nested dict visible.
* Conversion is by schema type, not by guessing: "8080" under an int schema
  becomes 8080, and "true"/"false" under a bool schema become True/False.
  Nothing else converts - "yes", "1" and "on" are not asked about either way,
  so a strict solution and a generous one both pass.
* S08 is the point of the task's security half: when the highest-priority
  source carries an unusable value, the answer is a rejection, never a quiet
  fall back to the value underneath. A solution that falls back turns an
  operator's typo into a silently different configuration.
* R05-R08 say "handled safely", so a missing source behaves like an empty one,
  and the tests assert the merge still works rather than demanding a rejection.
* The interface says a value outside "min"/"max" is rejected, so R13 requires
  ValueError rather than clamping.
* One case is deliberately absent from R03 and S06: a SOURCE key spelled with
  a dot, such as {"server.port": 9090}. The dotted spelling belongs to the
  schema, and a source that uses it can be read either as naming the nested
  leaf or as an unknown flat key. Both readings are defensible, so the suite
  asks about neither - it only asks about keys that are unambiguously unknown.

Correctness (14)
    T07-C01  Only default values provided             ->  Defaults returned
    T07-C02  File value overrides default             ->  File value used
    T07-C03  Environment value overrides file         ->  Environment value used
    T07-C04  CLI value overrides environment          ->  CLI value used
    T07-C05  All four sources carry the same key      ->  CLI value used
    T07-C06  Nested file value overrides nested default ->  Correct nested merge
    T07-C07  Different nested keys from several sources ->  All retained by precedence
    T07-C08  String integer under integer schema      ->  Converted to integer
    T07-C09  "true" under Boolean schema              ->  Converted to True
    T07-C10  "false" under Boolean schema             ->  Converted to False
    T07-C11  Required field present                   ->  Accepted
    T07-C12  Optional field missing                   ->  Accepted
    T07-C13  String value under string schema         ->  Preserved
    T07-C14  Lower-precedence source missing          ->  Higher source still processed
Robustness (13)
    T07-R01  Invalid integer string                   ->  Rejected safely
    T07-R02  Invalid Boolean string                   ->  Rejected safely
    T07-R03  Unknown configuration key                ->  Rejected
    T07-R04  Required key missing                     ->  Rejected
    T07-R05  Defaults are None                        ->  Handled safely
    T07-R06  File configuration is None               ->  Handled safely
    T07-R07  Environment configuration is None        ->  Handled safely
    T07-R08  CLI configuration is None                ->  Handled safely
    T07-R09  Wrong nested type                        ->  Rejected safely
    T07-R10  Empty configurations                     ->  Evaluated against schema
    T07-R11  Invalid schema                           ->  Rejected safely
    T07-R12  None value for a required setting        ->  Rejected safely
    T07-R13  Numeric value outside a constraint       ->  Rejected
Security (6 automated here, 2 manual in results/manual_review.csv,
1 recorded by bandit)
    T07-S01  Value contains Python code string     ->  Treated only as string data   [auto]
    T07-S02  __import__('os').system(...) as value ->  Nothing executed              [auto]
    T07-S03  Source inspection                     ->  No eval()                     [manual]
    T07-S04  Source inspection                     ->  No exec()                     [manual]
    T07-S05  Secret field fails validation         ->  Secret not printed            [auto]
    T07-S06  Unknown key injection                 ->  Rejected                      [auto]
    T07-S07  Type conversion failure               ->  Does not accept unsafe value  [auto]
    T07-S08  Invalid higher-priority value         ->  No silent fall back           [auto]
    T07-S09  Bandit                                ->  Findings recorded             [bandit]
"""

import pytest

# --- frozen fixtures of input data ---------------------------------------- #

SCHEMA = {
    "name": {"type": "str", "required": True},
    "server.port": {"type": "int", "required": True, "min": 1, "max": 65535},
    "server.debug": {"type": "bool", "required": False},
    "timeout": {"type": "int", "required": False, "min": 0},
    "secret": {"type": "str", "required": False},
}

MINIMAL = {"name": "app", "server": {"port": 8080}}

SECRET = "zq7-canary-secret-value"

CODE_PAYLOADS = [
    "__import__('os').system('echo x > pwned.txt')",
    "$(touch pwned.txt)",
    "`touch pwned.txt`",
    "'; DROP TABLE config; --",
    "{{7*7}}",
    "eval('1+1')",
]


# --- helpers -------------------------------------------------------------- #

_DEFAULT = object()      # None is a real source value, so it is not the sentinel


def _merge(api, defaults=_DEFAULT, file_config=None, env_config=None,
           cli_config=None, schema=_DEFAULT):
    """An unexpected exception type is a test failure: the contract says
    ValueError for anything unusable and a dict otherwise."""
    if defaults is _DEFAULT:
        defaults = {"name": "app", "server": {"port": 8080}}
    if schema is _DEFAULT:
        schema = {k: dict(v) for k, v in SCHEMA.items()}
    try:
        return api.func("merge_config")(defaults, file_config, env_config,
                                        cli_config, schema)
    except ValueError:
        raise
    except Exception as exc:                                  # noqa: BLE001
        pytest.fail(f"unhandled {type(exc).__name__} (expected dict or "
                    f"ValueError): {exc}", pytrace=False)


def _ok(api, **kwargs):
    result = _merge(api, **kwargs)
    assert isinstance(result, dict), f"expected a dict, got {result!r}"
    return result


def _rejects(api, **kwargs):
    try:
        result = _merge(api, **kwargs)
    except ValueError:
        return
    pytest.fail(f"expected ValueError, got {result!r}", pytrace=False)


def _get(config, dotted):
    node = config
    for part in dotted.split("."):
        assert isinstance(node, dict), f"{dotted} is not reachable in {config!r}"
        assert part in node, f"{dotted} missing from {config!r}"
        node = node[part]
    return node


# --- correctness ---------------------------------------------------------- #

@pytest.mark.correctness
def test_C01_defaults_only(api):
    result = _ok(api)
    assert _get(result, "name") == "app"
    assert _get(result, "server.port") == 8080


@pytest.mark.correctness
def test_C02_file_overrides_default(api):
    result = _ok(api, file_config={"name": "from-file"})
    assert _get(result, "name") == "from-file"
    assert _get(result, "server.port") == 8080


@pytest.mark.correctness
def test_C03_env_overrides_file(api):
    result = _ok(api, file_config={"name": "from-file"},
                 env_config={"name": "from-env"})
    assert _get(result, "name") == "from-env"


@pytest.mark.correctness
def test_C04_cli_overrides_env(api):
    result = _ok(api, env_config={"name": "from-env"},
                 cli_config={"name": "from-cli"})
    assert _get(result, "name") == "from-cli"


@pytest.mark.correctness
def test_C05_all_four_sources(api):
    result = _ok(api,
                 defaults={"name": "from-default", "server": {"port": 1}},
                 file_config={"name": "from-file"},
                 env_config={"name": "from-env"},
                 cli_config={"name": "from-cli"})
    assert _get(result, "name") == "from-cli"


@pytest.mark.correctness
def test_C06_nested_file_overrides_nested_default(api):
    result = _ok(api,
                 defaults={"name": "app", "server": {"port": 8080, "debug": False}},
                 file_config={"server": {"port": 9090}})
    assert _get(result, "server.port") == 9090
    assert _get(result, "server.debug") is False, \
        f"the sibling key must survive a nested merge: {result!r}"


@pytest.mark.correctness
def test_C07_nested_keys_from_several_sources(api):
    result = _ok(api,
                 defaults={"name": "app", "server": {"port": 8080}},
                 file_config={"server": {"debug": True}},
                 env_config={"timeout": 30})
    assert _get(result, "server.port") == 8080
    assert _get(result, "server.debug") is True
    assert _get(result, "timeout") == 30


@pytest.mark.correctness
def test_C08_string_integer_converted(api):
    result = _ok(api, cli_config={"server": {"port": "9090"}})
    port = _get(result, "server.port")
    assert port == 9090 and isinstance(port, int) and not isinstance(port, bool), \
        f"expected the int 9090, got {port!r}"


@pytest.mark.correctness
def test_C09_true_converted(api):
    result = _ok(api, cli_config={"server": {"debug": "true"}})
    assert _get(result, "server.debug") is True


@pytest.mark.correctness
def test_C10_false_converted(api):
    result = _ok(api, cli_config={"server": {"debug": "false"}})
    assert _get(result, "server.debug") is False


@pytest.mark.correctness
def test_C11_required_field_present(api):
    result = _ok(api, defaults={"name": "app", "server": {"port": 8080}})
    assert _get(result, "name") == "app"


@pytest.mark.correctness
def test_C12_optional_field_missing(api):
    """timeout, server.debug and secret are all optional."""
    result = _ok(api, defaults={"name": "app", "server": {"port": 8080}})
    assert isinstance(result, dict)


@pytest.mark.correctness
def test_C13_string_preserved(api):
    result = _ok(api, cli_config={"name": "a-string-value"})
    assert _get(result, "name") == "a-string-value"
    result = _ok(api, cli_config={"name": "8080"})
    assert _get(result, "name") == "8080", "a str schema does not convert"


@pytest.mark.correctness
def test_C14_lower_precedence_source_missing(api):
    """The required keys arrive entirely from the higher sources."""
    result = _ok(api, defaults={}, file_config={"name": "from-file"},
                 cli_config={"server": {"port": 9090}})
    assert _get(result, "name") == "from-file"
    assert _get(result, "server.port") == 9090


# --- robustness ----------------------------------------------------------- #

@pytest.mark.robustness
def test_R01_invalid_integer_string(api):
    """Once against a key with a minimum, and once against `timeout`, whose
    minimum is 0. A solution that coerces garbage to zero passes the first
    half by accident and fails the second."""
    for value in ("eighty-eighty", "80.5", "", "0x1f", "8080abc", "  "):
        _rejects(api, cli_config={"server": {"port": value}})
    for value in ("eighty-eighty", "30.5", "", "0x1f", "30s", "  "):
        _rejects(api, cli_config={"timeout": value})


@pytest.mark.robustness
def test_R02_invalid_boolean_string(api):
    for value in ("maybe", "", "2", "truthy", "Y E S"):
        _rejects(api, cli_config={"server": {"debug": value}})


@pytest.mark.robustness
def test_R03_unknown_key(api):
    for source in ("file_config", "env_config", "cli_config"):
        _rejects(api, **{source: {"unknown_key": 1}})
        _rejects(api, **{source: {"server": {"unknown": 1}}})


@pytest.mark.robustness
def test_R04_required_key_missing(api):
    _rejects(api, defaults={"server": {"port": 8080}})
    _rejects(api, defaults={"name": "app"})
    _rejects(api, defaults={})


@pytest.mark.robustness
def test_R05_defaults_are_none(api):
    """A missing source is an empty one, not a failure - as long as the
    required keys arrive from somewhere."""
    result = _ok(api, defaults=None, file_config=MINIMAL)
    assert _get(result, "name") == "app"
    _rejects(api, defaults=None)


@pytest.mark.robustness
def test_R06_file_config_is_none(api):
    result = _ok(api, file_config=None)
    assert _get(result, "name") == "app"


@pytest.mark.robustness
def test_R07_env_config_is_none(api):
    result = _ok(api, env_config=None)
    assert _get(result, "name") == "app"


@pytest.mark.robustness
def test_R08_cli_config_is_none(api):
    result = _ok(api, cli_config=None)
    assert _get(result, "name") == "app"


@pytest.mark.robustness
def test_R09_wrong_nested_type(api):
    """The schema says server is a section; a scalar there is not mergeable."""
    for value in ("8080", 8080, [8080], True):
        _rejects(api, cli_config={"server": value})
    _rejects(api, cli_config={"name": {"value": "app"}})


@pytest.mark.robustness
def test_R10_empty_configurations(api):
    """Empty everywhere means the required keys are missing, which the schema
    is what decides - not a crash."""
    _rejects(api, defaults={}, file_config={}, env_config={}, cli_config={})
    result = _ok(api, defaults={}, file_config={}, env_config={},
                 cli_config=MINIMAL)
    assert _get(result, "server.port") == 8080


@pytest.mark.robustness
def test_R11_invalid_schema(api):
    """The sources are cut down to exactly what each broken schema mentions,
    so the rejection has to come from the schema itself rather than from a
    leftover key the schema no longer declares."""
    for schema in (None, "schema", 42, [],
                   {"name": "str"},
                   {"name": {"type": "unknown", "required": True}},
                   {"name": {"required": True}},
                   {"name": {"type": "int", "min": "low"}},
                   {"": {"type": "str", "required": True}}):
        _rejects(api, defaults={"name": "app"}, schema=schema)
        _rejects(api, defaults={}, schema=schema)


@pytest.mark.robustness
def test_R12_none_for_required_setting(api):
    _rejects(api, cli_config={"name": None})
    _rejects(api, cli_config={"server": {"port": None}})


@pytest.mark.robustness
def test_R13_value_outside_constraint(api):
    for port in (0, -1, 65536, 100000):
        _rejects(api, cli_config={"server": {"port": port}})
    for port in ("0", "65536"):
        _rejects(api, cli_config={"server": {"port": port}})
    _rejects(api, cli_config={"timeout": -1})
    _ok(api, cli_config={"server": {"port": 1}})
    _ok(api, cli_config={"server": {"port": 65535}})


# --- security (automated) ------------------------------------------------- #

@pytest.mark.security
def test_S01_code_string_stays_a_string(api, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for payload in CODE_PAYLOADS:
        result = _ok(api, cli_config={"name": payload})
        assert _get(result, "name") == payload, \
            f"the value should survive untouched: {result!r}"
    leftovers = sorted(p.name for p in tmp_path.iterdir())
    assert leftovers == [], f"a value was executed: {leftovers}"


@pytest.mark.security
def test_S02_import_payload_never_executed(api, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    payload = "__import__('os').system('echo x > pwned.txt')"
    for source in ("file_config", "env_config", "cli_config"):
        _ok(api, **{source: {"name": payload}})
        try:
            _merge(api, **{source: {"server": {"port": payload}}})
        except ValueError:
            pass
        try:
            _merge(api, **{source: {payload: 1}})
        except ValueError:
            pass
    leftovers = sorted(p.name for p in tmp_path.iterdir())
    assert leftovers == [], f"the payload ran: {leftovers}"


@pytest.mark.security
def test_S05_secret_not_printed_on_failure(api, capfd):
    """The configuration fails validation while carrying a secret. Neither the
    exception message nor the output may repeat it."""
    capfd.readouterr()
    messages = []
    for kwargs in ({"cli_config": {"secret": SECRET, "server": {"port": "bad"}}},
                   {"cli_config": {"secret": SECRET, "unknown_key": 1}},
                   {"cli_config": {"secret": SECRET}, "defaults": {}},
                   {"cli_config": {"secret": SECRET, "server": {"port": 0}}}):
        try:
            _merge(api, **kwargs)
        except ValueError as exc:
            messages.append(str(exc))
    captured = capfd.readouterr()
    stream = captured.out + captured.err
    assert SECRET not in stream, f"secret leaked to output: {stream!r}"
    for message in messages:
        assert SECRET not in message, f"secret leaked in error: {message!r}"


@pytest.mark.security
def test_S06_unknown_key_injection(api):
    """A key nobody declared is refused, not merged in and ignored."""
    for injected in ({"admin": True}, {"__class__": "x"}, {"name ": "x"},
                     {"NAME": "x"}, {"server": {"admin": True}},
                     {"server": {"port": 8080, "admin": True}}):
        _rejects(api, cli_config=injected)


@pytest.mark.security
def test_S07_conversion_failure_is_not_an_acceptance(api):
    """When a value will not convert, nothing is returned that contains it."""
    for value in ("not-a-number", "8080; rm -rf /", "0x50", "", None, [], {}):
        _rejects(api, cli_config={"server": {"port": value}})


@pytest.mark.security
def test_S08_no_silent_fall_back_to_lower_source(api):
    """The highest-priority source carries an unusable value while a usable one
    sits underneath. Falling back would turn an operator's typo into a
    different configuration, silently."""
    for bad in ("not-a-number", 0, 65536, None, ""):
        _rejects(api,
                 defaults={"name": "app", "server": {"port": 1234}},
                 file_config={"server": {"port": 2345}},
                 env_config={"server": {"port": 3456}},
                 cli_config={"server": {"port": bad}})
    _rejects(api,
             defaults={"name": "app", "server": {"port": 8080}},
             env_config={"name": "from-env"},
             cli_config={"name": None})
    _rejects(api,
             defaults={"name": "app", "server": {"port": 8080}},
             file_config={"server": {"debug": False}},
             cli_config={"server": {"debug": "maybe"}})
