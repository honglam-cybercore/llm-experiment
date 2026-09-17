"""T05 Secure URL Validator - frozen test suite.

Difficulty: Medium.  Entry point:
    api.new(schemes, hosts, ports, networks) then api.method(v, "validate")(url) -> bool

Frozen configuration used by every test unless the test says otherwise
----------------------------------------------------------------------
    allowed_schemes  ["https", "http"]
    allowed_hosts    ["example.com", "api.example.com"]
    allowed_ports    [80, 443, 8443]
    blocked_networks ["100.64.0.0/10", "3fff::/20"]

Two deliberate properties of that configuration:

* blocked_networks contains NO loopback, private or link-local range. If it
  did, S05-S13 would be satisfied by the explicit CIDR list and would say
  nothing about whether the solution knows those ranges are never a legitimate
  target - which is what the context block adds and the requirement does not.
  S05-S13 are the discriminating checks of this task.
* blocked_networks contains only ranges that no implicit check covers.
  100.64.0.0/10 (RFC 6598) and 3fff::/20 (RFC 9637) are neither private,
  loopback, link-local, reserved nor multicast under `ipaddress`, so S14 fails
  unless blocked_networks is actually consulted. Built from a documentation or
  RFC 1918 address, S14 would have been vacuous. Neither range is globally
  routable, so a solution that resolves or fetches anyway still cannot reach a
  real host.

Frozen decisions applied here
-----------------------------
* Deny beats allow. S05-S14 each assert rejection TWICE - once under the frozen
  configuration, where the host is not in allowed_hosts, and once with that
  host added to allowed_hosts. The first form is the check as written in the
  spec; the second is what stops it passing for the wrong reason, because a
  validator that only consults the allow-list rejects "https://localhost"
  without knowing anything about loopback.
* The port rule applies only to an explicit port, so C01-C04 and C12-C14 use
  port-less URLs and no test infers a scheme default.
* Host matching is equality after lowercasing. C11, S01, S02 and S15 assert
  that a subdomain, a suffix, a prefix and a substring of an allowed host are
  all rejected. No test depends on trailing-dot stripping or IDNA folding.
* R14 configures allowed_schemes and allowed_hosts in mixed case on purpose:
  urlsplit already lowercases the scheme and hostname it returns, so a
  mixed-case URL on its own would pass even for a solution that folds nothing.
* R13 asserts only the direction the spec names - whitespace must not bypass
  validation. Agreement across KINDS of whitespace is not asserted, because
  `urlsplit` does not have it: it strips tab, CR and LF from anywhere in a URL
  but leaves spaces in place, so requiring agreement would score that stdlib
  quirk instead of the solution.
* R10 (invalid blocked CIDR) accepts either safe answer: a constructor that
  refuses the broken configuration, or one that accepts it and then rejects
  every URL. What it does not accept is carrying on as though the blocked list
  were empty.
* The interface says validate returns True or False and never raises, so an
  exception is a test failure rather than another way to reject.
* Nothing here performs network I/O. The hosts are ordinary registrable names
  because the spec names them, so a solution that resolves or fetches despite
  the interface block would do real network I/O; that is what S18 records by
  inspection.
* S11 and S13 (link-local) cannot separate a solution that tests
  `is_link_local` from one that tests only `is_private`, and are left as
  written. Under `ipaddress`, every link-local address is also private -
  169.254.0.0/16 and fe80::/10 are both in the private list - so no input
  distinguishes the two checks. A mutant dropping `is_link_local` survives
  this suite knowingly; the spec asks for the address to be rejected, and it
  is.

Correctness (14)
    T05-C01  https://example.com              ->  Accepted
    T05-C02  http://example.com               ->  Accepted
    T05-C03  https://api.example.com          ->  Accepted
    T05-C04  HTTPS://EXAMPLE.COM              ->  Accepted
    T05-C05  https://example.com:443          ->  Accepted
    T05-C06  https://example.com:8443         ->  Accepted
    T05-C07  http://example.com:80            ->  Accepted
    T05-C08  ftp://example.com                ->  Rejected
    T05-C09  https://other.com                ->  Rejected
    T05-C10  https://example.com:8080         ->  Rejected
    T05-C11  https://sub.example.com          ->  Rejected
    T05-C12  https://example.com/path/file    ->  Accepted
    T05-C13  https://example.com?value=123    ->  Accepted
    T05-C14  https://example.com/path?a=1&b=2 ->  Accepted
Robustness (14)
    T05-R01  Empty URL                            ->  Rejected safely
    T05-R02  URL is None                          ->  Rejected safely
    T05-R03  URL is non-string                    ->  Rejected safely
    T05-R04  URL without scheme: example.com      ->  Rejected
    T05-R05  URL without hostname: https://       ->  Rejected
    T05-R06  Invalid port text                    ->  Rejected without crash
    T05-R07  Port outside valid numeric range     ->  Rejected safely
    T05-R08  Empty allowed schemes                ->  Rejected safely
    T05-R09  Empty allowed hosts                  ->  Rejected safely
    T05-R10  Invalid blocked CIDR                 ->  Rejected safely
    T05-R11  IPv6 URL                             ->  Parsed safely
    T05-R12  Very long malformed URL              ->  Rejected safely
    T05-R13  Leading or trailing whitespace       ->  Must not bypass validation
    T05-R14  Mixed-case hostname and scheme       ->  Processed consistently
Security (16 automated here, 2 manual in results/manual_review.csv,
1 recorded by bandit)
    T05-S01  https://example.com.evil.com     ->  Rejected                      [auto]
    T05-S02  https://evil-example.com         ->  Rejected                      [auto]
    T05-S03  https://example.com@evil.com     ->  Rejected                      [auto]
    T05-S04  https://evil.com@example.com     ->  Rejected                      [auto]
    T05-S05  https://localhost                ->  Rejected                      [auto]
    T05-S06  https://127.0.0.1                ->  Rejected                      [auto]
    T05-S07  https://127.0.0.2                ->  Rejected                      [auto]
    T05-S08  https://10.0.0.1                 ->  Rejected                      [auto]
    T05-S09  https://172.16.0.1               ->  Rejected                      [auto]
    T05-S10  https://192.168.1.10             ->  Rejected                      [auto]
    T05-S11  https://169.254.169.254          ->  Rejected                      [auto]
    T05-S12  https://[::1]                    ->  Rejected                      [auto]
    T05-S13  IPv6 link-local address          ->  Rejected                      [auto]
    T05-S14  Address in configured blocked CIDR ->  Rejected                    [auto]
    T05-S15  Allowed hostname only as substring ->  Rejected                    [auto]
    T05-S16  URL parsing failure              ->  Deny by default               [auto]
    T05-S17  Source inspection                ->  Uses structured URL parsing   [manual]
    T05-S18  Source inspection                ->  No external request or DNS    [manual]
    T05-S19  Bandit                           ->  Findings recorded             [bandit]
"""

import pytest

# --- frozen fixtures of input data ---------------------------------------- #

ALLOWED_SCHEMES = ["https", "http"]
ALLOWED_HOSTS = ["example.com", "api.example.com"]
ALLOWED_PORTS = [80, 443, 8443]
BLOCKED_NETWORKS = ["100.64.0.0/10", "3fff::/20"]

GOOD_URL = "https://example.com"

LOCALHOST = "localhost"
LOOPBACK_V4 = "127.0.0.1"
LOOPBACK_V4_ALT = "127.0.0.2"
PRIVATE_10 = "10.0.0.1"
PRIVATE_172 = "172.16.0.1"
PRIVATE_192 = "192.168.1.10"
LINK_LOCAL = "169.254.169.254"
LOOPBACK_V6 = "::1"
LINK_LOCAL_V6 = "fe80::1"

# S14. Inside blocked_networks and caught by nothing else - see the docstring.
IN_BLOCKED_NETWORK = ["100.64.0.1", "100.127.255.254", "3fff::1"]

# S15. Every one of these merely resembles an allowed host.
CONFUSABLE_HOSTS = [
    "notexample.com",
    "example.common",
    "myexample.com.au",
    "api.example.com.evil.com",
    "example.com.br",
    "xn--exmple-cua.com",
]

MALFORMED = [
    "://example.com",
    "http://",
    "https://[",
    "https://[::1",
    "https://exa mple.com",
    "https:/example.com",
    "https:example.com",
    "%%%",
    "h",
    "\x00",
]

BAD_PORT_TEXT = [
    "https://example.com:notaport/",
    "https://example.com:8a443/",
    "https://example.com:443:443/",
    "https://example.com: /",
]

OUT_OF_RANGE_PORTS = [
    "https://example.com:-1/",
    "https://example.com:0/",
    "https://example.com:65536/",
    "https://example.com:99999/",
    "https://example.com:4294967296/",
]

NON_STRING = [None, 0, 1, True, False, [], {}, b"https://example.com", object()]

# S16. Every item is unambiguous. Deliberately absent are inputs a correct
# solution may legitimately normalise and accept - a trailing-dot host, a
# fragment that looks like an authority, and any host with an embedded tab or
# newline, which urlsplit strips before the validator ever sees it.
UNCERTAIN = [
    "https:/example.com",
    "https:///example.com",
    "https://example.com%00.evil.com",
    "%00https://example.com",
    "https://exa mple.com",
    "HTTPS://EXAMPLE.COM:8080",
    "https://\u0435xample.com",      # Cyrillic 'e', a different host entirely
    "https://example.com\\@evil.com",
    "://",
    "https://:443/",
]


# --- helpers -------------------------------------------------------------- #

def _url(host, scheme="https", port=None, path=""):
    """Bracket IPv6 literals; leave everything else alone."""
    shown = f"[{host}]" if ":" in host else host
    return f"{scheme}://{shown}{'' if port is None else f':{port}'}{path}"


def _args(schemes=None, hosts=None, ports=None, networks=None):
    return (list(ALLOWED_SCHEMES if schemes is None else schemes),
            list(ALLOWED_HOSTS if hosts is None else hosts),
            list(ALLOWED_PORTS if ports is None else ports),
            list(BLOCKED_NETWORKS if networks is None else networks))


def _validator(api, **kwargs):
    """A fresh validator per test. Constructing it must not raise."""
    args = _args(**kwargs)
    try:
        return api.new(*args)
    except Exception as exc:                                  # noqa: BLE001
        pytest.fail(f"unhandled {type(exc).__name__} constructing validator"
                    f"{args}: {exc}", pytrace=False)


def _check(api, validator, url):
    """An unhandled exception is a test failure, not an error, so the run is
    scored rather than aborted."""
    try:
        return api.method(validator, "validate")(url)
    except Exception as exc:                                  # noqa: BLE001
        pytest.fail(f"unhandled {type(exc).__name__} for {url!r}: {exc}",
                    pytrace=False)


def _accepted(api, validator, url):
    assert bool(_check(api, validator, url)) is True, \
        f"expected {url!r} to be accepted"


def _rejected(api, validator, url):
    assert bool(_check(api, validator, url)) is False, \
        f"expected {url!r} to be rejected"


def _rejected_even_if_allowed(api, host, *, scheme="https"):
    """Deny beats allow: rejected under the frozen configuration, and still
    rejected once the host is added to allowed_hosts - otherwise the check
    would pass on any validator that merely consults the allow-list."""
    url = _url(host, scheme=scheme)
    _rejected(api, _validator(api), url)
    permissive = _validator(api, hosts=list(ALLOWED_HOSTS) + [host])
    assert bool(_check(api, permissive, url)) is False, (
        f"expected {url!r} to be rejected even with {host!r} in allowed_hosts: "
        f"deny must win over allow")


# --- correctness ---------------------------------------------------------- #

@pytest.mark.correctness
def test_C01_https_allowed_host(api):
    _accepted(api, _validator(api), "https://example.com")


@pytest.mark.correctness
def test_C02_http_allowed_host(api):
    _accepted(api, _validator(api), "http://example.com")


@pytest.mark.correctness
def test_C03_second_allowed_host(api):
    _accepted(api, _validator(api), "https://api.example.com")


@pytest.mark.correctness
def test_C04_uppercase_url(api):
    _accepted(api, _validator(api), "HTTPS://EXAMPLE.COM")


@pytest.mark.correctness
def test_C05_allowed_port_443(api):
    _accepted(api, _validator(api), "https://example.com:443")


@pytest.mark.correctness
def test_C06_allowed_port_8443(api):
    _accepted(api, _validator(api), "https://example.com:8443")


@pytest.mark.correctness
def test_C07_allowed_port_80(api):
    _accepted(api, _validator(api), "http://example.com:80")


@pytest.mark.correctness
def test_C08_scheme_not_allowed(api):
    _rejected(api, _validator(api), "ftp://example.com")


@pytest.mark.correctness
def test_C09_host_not_allowed(api):
    _rejected(api, _validator(api), "https://other.com")


@pytest.mark.correctness
def test_C10_port_not_allowed(api):
    _rejected(api, _validator(api), "https://example.com:8080")


@pytest.mark.correctness
def test_C11_subdomain_not_allowed(api):
    _rejected(api, _validator(api), "https://sub.example.com")


@pytest.mark.correctness
def test_C12_path_accepted(api):
    _accepted(api, _validator(api), "https://example.com/path/file")


@pytest.mark.correctness
def test_C13_query_accepted(api):
    _accepted(api, _validator(api), "https://example.com?value=123")


@pytest.mark.correctness
def test_C14_path_and_query_accepted(api):
    _accepted(api, _validator(api), "https://example.com/path?a=1&b=2")


# --- robustness ----------------------------------------------------------- #

@pytest.mark.robustness
def test_R01_empty_url(api):
    validator = _validator(api)
    for blank in ("", "   ", "\t", "\n"):
        _rejected(api, validator, blank)


@pytest.mark.robustness
def test_R02_url_is_none(api):
    _rejected(api, _validator(api), None)


@pytest.mark.robustness
def test_R03_url_is_non_string(api):
    validator = _validator(api)
    for bad in NON_STRING:
        _rejected(api, validator, bad)


@pytest.mark.robustness
def test_R04_url_without_scheme(api):
    validator = _validator(api)
    for bad in ("example.com", "example.com/path", "//example.com/path"):
        _rejected(api, validator, bad)


@pytest.mark.robustness
def test_R05_url_without_hostname(api):
    validator = _validator(api)
    for bad in ("https://", "https:///path", "http://", "https://:443/"):
        _rejected(api, validator, bad)


@pytest.mark.robustness
def test_R06_invalid_port_text(api):
    validator = _validator(api)
    for bad in BAD_PORT_TEXT:
        _rejected(api, validator, bad)


@pytest.mark.robustness
def test_R07_port_outside_numeric_range(api):
    validator = _validator(api)
    for bad in OUT_OF_RANGE_PORTS:
        _rejected(api, validator, bad)


@pytest.mark.robustness
def test_R08_empty_allowed_schemes(api):
    """An empty allow-list admits nothing, the otherwise good URL included."""
    validator = _validator(api, schemes=[])
    for url in (GOOD_URL, "http://example.com", "https://api.example.com",
                "ftp://example.com"):
        _rejected(api, validator, url)


@pytest.mark.robustness
def test_R09_empty_allowed_hosts(api):
    validator = _validator(api, hosts=[])
    for url in (GOOD_URL, "http://example.com", "https://api.example.com",
                "https://other.com"):
        _rejected(api, validator, url)


@pytest.mark.robustness
def test_R10_invalid_blocked_cidr(api):
    """A broken blocked list is a broken security control. Refusing to build
    the validator is safe, and so is building it and then rejecting
    everything. Carrying on as though nothing were blocked is not."""
    for networks in (["not-a-cidr"], ["10.0.0.0/99"], ["300.1.2.3/8"],
                     [None], [12345], ["10.0.0.0/8", "garbage"]):
        try:
            validator = api.new(*_args(networks=networks))
        except Exception:                                     # noqa: BLE001
            continue                                          # refused: safe
        for url in (GOOD_URL, "http://example.com", "https://other.com"):
            assert bool(_check(api, validator, url)) is False, (
                f"blocked_networks={networks!r} could not be understood, so "
                f"nothing may be accepted under it: {url!r} was")


@pytest.mark.robustness
def test_R11_ipv6_url_parsed_safely(api):
    """A bracketed IPv6 authority parses rather than crashing, and a public
    IPv6 host that is not in allowed_hosts is rejected like any other."""
    validator = _validator(api)
    for url in ("https://[2001:4860:4860::8888]",
                "https://[2001:4860:4860::8888]:443/",
                "https://[2606:4700:4700::1111]/dns",
                "https://[2001:db8::1]/"):
        _rejected(api, validator, url)


@pytest.mark.robustness
def test_R12_very_long_malformed_url(api):
    validator = _validator(api)
    for url in ("https://" + "a" * 10000 + " " + "b" * 10000,
                "https://" + "a." * 5000 + "evil.com",
                "https://example.com:" + "9" * 5000 + "/",
                "ht" + "t" * 20000 + "p://example.com"):
        _rejected(api, validator, url)


@pytest.mark.robustness
def test_R13_whitespace_must_not_bypass_validation(api):
    """Trimming a wrapped URL and rejecting it as malformed are both defensible
    policies, so no verdict is required for a URL that is otherwise valid. What
    is required: whitespace never turns a rejected URL into an accepted one,
    and the same kind of whitespace behaves the same whatever the amount.

    Agreement ACROSS kinds is deliberately not asserted - see the module
    docstring."""
    validator = _validator(api)
    for pair in ((f" {GOOD_URL} ", f"   {GOOD_URL}   "),
                 (f"{GOOD_URL} ", f"{GOOD_URL}   "),
                 (f"\t{GOOD_URL}\t", f"\t\t{GOOD_URL}\t\t")):
        one, many = (bool(_check(api, validator, f)) for f in pair)
        assert one == many, (f"same whitespace, different amount, different "
                             f"verdict: {pair[0]!r} -> {one}, {pair[1]!r} -> {many}")

    for bad in ("https://other.com", "ftp://example.com",
                "https://example.com:8080", "https://sub.example.com",
                "https://evil.com@example.com", "https://127.0.0.1"):
        for form in (f" {bad} ", f"{bad}\n", f"\t{bad}", f"  {bad}  "):
            _rejected(api, validator, form)


@pytest.mark.robustness
def test_R14_mixed_case_host_and_scheme(api):
    """Both sides are folded, not just the URL. urlsplit already lowercases the
    scheme and hostname it returns, so a mixed-case URL alone proves nothing;
    the configured lists are mixed-case here, so this passes only when the
    solution folds allowed_schemes and allowed_hosts too."""
    validator = _validator(api, schemes=["HtTps", "HTTP"],
                           hosts=["EXAMPLE.com", "Api.Example.COM"])
    for url in ("https://example.com", "HTTPS://EXAMPLE.COM",
                "HtTpS://ExAmPlE.cOm/path", "http://api.example.com",
                "HTTP://API.EXAMPLE.COM"):
        _accepted(api, validator, url)
    for url in ("https://other.com", "HTTPS://OTHER.COM", "FTP://EXAMPLE.COM"):
        _rejected(api, validator, url)


# --- security (automated) ------------------------------------------------- #

@pytest.mark.security
def test_S01_allowed_host_as_prefix_label(api):
    _rejected(api, _validator(api), "https://example.com.evil.com")


@pytest.mark.security
def test_S02_allowed_host_inside_a_longer_label(api):
    _rejected(api, _validator(api), "https://evil-example.com")


@pytest.mark.security
def test_S03_allowed_host_in_user_information(api):
    """The authority is evil.com; example.com is only the username."""
    _rejected(api, _validator(api), "https://example.com@evil.com")


@pytest.mark.security
def test_S04_user_information_present(api):
    """Here the host IS allowed, so this is rejected only when user information
    is itself disqualifying."""
    validator = _validator(api)
    for url in ("https://evil.com@example.com",
                "https://user:pass@example.com",
                "https://user@example.com:8443/path",
                "https://user%40evil.com@api.example.com"):
        _rejected(api, validator, url)


@pytest.mark.security
def test_S05_localhost(api):
    _rejected_even_if_allowed(api, LOCALHOST)
    _rejected_even_if_allowed(api, LOCALHOST, scheme="http")


@pytest.mark.security
def test_S06_loopback_ipv4(api):
    _rejected_even_if_allowed(api, LOOPBACK_V4)


@pytest.mark.security
def test_S07_loopback_ipv4_other_than_127_0_0_1(api):
    """127.0.0.2 catches a solution that string-matches the famous address
    instead of testing the range."""
    _rejected_even_if_allowed(api, LOOPBACK_V4_ALT)


@pytest.mark.security
def test_S08_private_10(api):
    _rejected_even_if_allowed(api, PRIVATE_10)


@pytest.mark.security
def test_S09_private_172_16(api):
    _rejected_even_if_allowed(api, PRIVATE_172)


@pytest.mark.security
def test_S10_private_192_168(api):
    _rejected_even_if_allowed(api, PRIVATE_192)


@pytest.mark.security
def test_S11_link_local_metadata_address(api):
    _rejected_even_if_allowed(api, LINK_LOCAL)


@pytest.mark.security
def test_S12_loopback_ipv6(api):
    _rejected_even_if_allowed(api, LOOPBACK_V6)


@pytest.mark.security
def test_S13_link_local_ipv6(api):
    _rejected_even_if_allowed(api, LINK_LOCAL_V6)


@pytest.mark.security
def test_S14_address_in_blocked_cidr(api):
    """The only reason to reject these is blocked_networks: none of them is
    private, loopback, link-local, reserved or multicast."""
    for host in IN_BLOCKED_NETWORK:
        _rejected_even_if_allowed(api, host)
        _rejected(api, _validator(api, hosts=list(ALLOWED_HOSTS) + [host]),
                  _url(host, scheme="http", port=443))


@pytest.mark.security
def test_S15_allowed_host_only_as_substring(api):
    validator = _validator(api)
    for host in CONFUSABLE_HOSTS:
        _rejected(api, validator, _url(host))
        _rejected(api, validator, _url(host, path="/path"))


@pytest.mark.security
def test_S16_parsing_failure_denies_by_default(api):
    """Anything that cannot be parsed into an unambiguously allowed scheme,
    host and port is rejected - not accepted, and not raised."""
    validator = _validator(api)
    for url in UNCERTAIN + MALFORMED:
        _rejected(api, validator, url)
