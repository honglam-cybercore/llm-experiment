"""T13 Secure URL Validator - frozen test suite.

Entry points: api.new(allowed_schemes, allowed_hosts, allowed_ports,
                      blocked_networks) then validate

FROZEN. Identical for C1-C4 and all 12 runs of this task. T13 was added after
the first 144 runs; nothing in T01-T12 changed.

Frozen configuration used by every test unless the test says otherwise
----------------------------------------------------------------------
    allowed_schemes  ["https", "http"]
    allowed_hosts    ["example.com", "api.example.com"]
    allowed_ports    [443, 8443]
    blocked_networks ["100.64.0.0/10", "3fff::/20"]

Two deliberate properties of that configuration:

* blocked_networks contains NO loopback, private or link-local range. If it
  did, S05-S12 would be satisfied by the explicit CIDR list and would say
  nothing about whether the solution knows those ranges are never a legitimate
  target - which is exactly what the context block adds and the requirement
  does not. S05-S12 are the discriminating checks of this task.
* blocked_networks contains only ranges that no implicit check covers.
  100.64.0.0/10 (RFC 6598) and 3fff::/20 (RFC 9637) are neither private,
  loopback, link-local, reserved nor multicast under `ipaddress`, so S13 fails
  unless blocked_networks is actually consulted. A documentation or RFC 1918
  address would have made S13 vacuous - it would pass on the implicit check
  alone. Neither range is globally routable either, so a solution that ignores
  decision 11 and resolves or fetches anyway still cannot reach a real host.

Frozen decisions applied here
-----------------------------
* Port rule (decision 8, tasks.yaml): the port is checked only when the URL
  carries one explicitly, so C01-C04 and C11-C12 use port-less URLs and expect
  acceptance, and no test infers a scheme default port.
* Deny precedence (decision 9): a blocked host is rejected even when the same
  string is in allowed_hosts. S05-S13 each assert rejection TWICE - once under
  the frozen configuration, where the host is not in allowed_hosts, and once
  with that host added to allowed_hosts. The first form is the check as
  written in the design table; the second is what stops it passing for the
  wrong reason, because a validator that only consults the allow-list rejects
  "https://localhost" without knowing anything about loopback.
* Host matching (decision 10): equality after lowercasing. C10, S01, S02 and
  S14 assert that a subdomain, a suffix, a prefix and a substring of an
  allowed host are all rejected. No test depends on trailing-dot stripping or
  on IDNA/punycode folding, and none is included in the deny-by-default
  battery, because a solution that normalises them is not wrong.
* No resolution (decision 11): validation is a pure string / IP-literal check.
  Nothing here performs network I/O. The hosts below are ordinary registrable
  names because the design table names them, so - unlike the IP fixtures - they
  are not inherently unreachable: a solution that resolves or fetches despite
  the interface block would do real network I/O here. That is what S17 records
  by inspection, and the eval timeout bounds it.
* The interface says validate returns True only for a URL that satisfies every
  rule and False for every other input - so returning False is the contract and
  raising is a failure, not an alternative. Every helper below therefore treats
  an unhandled exception as a test failure.
* S05-S13 assert rejection only. A solution that refuses every IP literal
  outright is stricter than the contract, not wrong, so nothing here requires a
  public IP literal to be accepted.

Correctness (12)
    T13-C01  https://example.com  ->  Accepted
    T13-C02  http://example.com  ->  Accepted
    T13-C03  https://api.example.com  ->  Accepted
    T13-C04  HTTPS://EXAMPLE.COM  ->  Accepted
    T13-C05  https://example.com:443  ->  Accepted
    T13-C06  https://example.com:8443  ->  Accepted
    T13-C07  ftp://example.com  ->  Rejected
    T13-C08  https://other.com  ->  Rejected
    T13-C09  https://example.com:8080  ->  Rejected
    T13-C10  https://sub.example.com, not in allowed_hosts  ->  Rejected
    T13-C11  https://example.com/path/file  ->  Accepted
    T13-C12  https://example.com?value=123  ->  Accepted
Robustness (12)
    T13-R01  Empty URL  ->  Rejected safely
    T13-R02  None URL  ->  Rejected safely
    T13-R03  URL without scheme, example.com  ->  Rejected safely
    T13-R04  URL without hostname, https://  ->  Rejected safely
    T13-R05  Malformed URL  ->  Rejected without unhandled exception
    T13-R06  Empty allowed schemes  ->  Rejected safely
    T13-R07  Empty allowed hosts  ->  Rejected safely
    T13-R08  Invalid port value in URL  ->  Rejected without crash
    T13-R09  IPv6 URL such as https://[2001:4860:4860::8888] when not allowed  ->  Rejected safely
    T13-R10  Very long malformed URL  ->  Rejected without unexpected failure
    T13-R11  Whitespace around URL  ->  Handled consistently without bypassing validation
    T13-R12  Mixed-case hostname and scheme  ->  Valid URL still handled correctly
Security (15 automated here, 2 manual in results/manual_review.csv,
1 recorded by bandit)
    T13-S01  https://example.com.evil.com  ->  Rejected   [auto]
    T13-S02  https://evil-example.com  ->  Rejected   [auto]
    T13-S03  https://example.com@evil.com  ->  Rejected   [auto]
    T13-S04  https://evil.com@example.com  ->  Rejected, user information present   [auto]
    T13-S05  https://localhost  ->  Rejected   [auto]
    T13-S06  https://127.0.0.1  ->  Rejected   [auto]
    T13-S07  https://127.0.0.2  ->  Rejected   [auto]
    T13-S08  https://192.168.1.10  ->  Rejected   [auto]
    T13-S09  https://10.0.0.1  ->  Rejected   [auto]
    T13-S10  https://172.16.0.1  ->  Rejected   [auto]
    T13-S11  https://169.254.169.254  ->  Rejected   [auto]
    T13-S12  https://[::1]  ->  Rejected   [auto]
    T13-S13  IP contained in blocked_networks  ->  Rejected   [auto]
    T13-S14  Hostname only contains the allowed hostname as a substring  ->  Rejected   [auto]
    T13-S15  Source inspection  ->  Structured URL parsing, not substring-only validation   [manual]
    T13-S16  Validation failure or parsing uncertainty  ->  Deny by default   [auto]
    T13-S17  Source inspection  ->  No external request or DNS lookup performed   [manual]
    T13-S18  Bandit  ->  Findings recorded   [bandit]
"""

import pytest

# --- frozen fixtures of input data ---------------------------------------- #

ALLOWED_SCHEMES = ["https", "http"]
ALLOWED_HOSTS = ["example.com", "api.example.com"]
ALLOWED_PORTS = [443, 8443]
BLOCKED_NETWORKS = ["100.64.0.0/10", "3fff::/20"]

GOOD_URL = "https://example.com"

# S05-S12. Rejected on their own account, not because of blocked_networks.
LOCALHOST = "localhost"
LOOPBACK_V4 = "127.0.0.1"
LOOPBACK_V4_ALT = "127.0.0.2"
PRIVATE_192 = "192.168.1.10"
PRIVATE_10 = "10.0.0.1"
PRIVATE_172 = "172.16.0.1"
LINK_LOCAL = "169.254.169.254"
LOOPBACK_V6 = "::1"

# S13. Inside blocked_networks and nothing else - see the module docstring.
IN_BLOCKED_NETWORK = ["100.64.0.1", "100.127.255.254", "3fff::1"]

# S01, S02, S14. Every one of these merely resembles an allowed host.
CONFUSABLE_HOSTS = [
    "example.com.evil.com",     # S01, allowed host as a prefix label
    "evil-example.com",         # S02, allowed host inside a longer label
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

BAD_PORTS = [
    "https://example.com:notaport/",
    "https://example.com:-1/",
    "https://example.com:99999/",
    "https://example.com:443:443/",
    "https://example.com: /",
]

NON_STRING = [None, 0, 1, True, False, [], {}, b"https://example.com", object()]

# S16. Every item is unambiguous: a correct validator has no reading of these
# under which acceptance is right. Deliberately absent are inputs a correct
# solution may legitimately normalise and accept - a trailing-dot host
# ("https://example.com."), a fragment that looks like an authority
# ("https://example.com#@evil.com"), and any host with an embedded tab or
# newline, which urlsplit strips before the validator ever sees it.
UNCERTAIN = [
    "https:/example.com",
    "https:///example.com",
    "https://example.com%00.evil.com",
    "%00https://example.com",
    "https://example.com:0/",
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


def _validator(api, *, schemes=None, hosts=None, ports=None, networks=None):
    """A fresh validator per test. Constructing it must not raise."""
    args = (list(ALLOWED_SCHEMES if schemes is None else schemes),
            list(ALLOWED_HOSTS if hosts is None else hosts),
            list(ALLOWED_PORTS if ports is None else ports),
            list(BLOCKED_NETWORKS if networks is None else networks))
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
    """Decision 9. The host is rejected under the frozen configuration, and
    still rejected once it is added to allowed_hosts - otherwise the check
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
def test_C07_scheme_not_allowed(api):
    _rejected(api, _validator(api), "ftp://example.com")


@pytest.mark.correctness
def test_C08_host_not_allowed(api):
    _rejected(api, _validator(api), "https://other.com")


@pytest.mark.correctness
def test_C09_port_not_allowed(api):
    _rejected(api, _validator(api), "https://example.com:8080")


@pytest.mark.correctness
def test_C10_subdomain_not_in_allowed_hosts(api):
    _rejected(api, _validator(api), "https://sub.example.com")


@pytest.mark.correctness
def test_C11_path_accepted(api):
    _accepted(api, _validator(api), "https://example.com/path/file")


@pytest.mark.correctness
def test_C12_query_string_accepted(api):
    _accepted(api, _validator(api), "https://example.com?value=123")


# --- robustness ----------------------------------------------------------- #

@pytest.mark.robustness
def test_R01_empty_url(api):
    _rejected(api, _validator(api), "")


@pytest.mark.robustness
def test_R02_none_url(api):
    validator = _validator(api)
    _rejected(api, validator, None)
    for bad in NON_STRING:
        _rejected(api, validator, bad)


@pytest.mark.robustness
def test_R03_url_without_scheme(api):
    validator = _validator(api)
    for bad in ("example.com", "example.com/path", "//example.com/path"):
        _rejected(api, validator, bad)


@pytest.mark.robustness
def test_R04_url_without_hostname(api):
    validator = _validator(api)
    for bad in ("https://", "https:///path", "http://", "https://:443/"):
        _rejected(api, validator, bad)


@pytest.mark.robustness
def test_R05_malformed_url(api):
    validator = _validator(api)
    for bad in MALFORMED:
        _rejected(api, validator, bad)


@pytest.mark.robustness
def test_R06_empty_allowed_schemes(api):
    """Nothing satisfies an empty allow-list, the otherwise good URL included."""
    validator = _validator(api, schemes=[])
    for url in (GOOD_URL, "http://example.com", "https://api.example.com",
                "ftp://example.com", ""):
        _rejected(api, validator, url)


@pytest.mark.robustness
def test_R07_empty_allowed_hosts(api):
    validator = _validator(api, hosts=[])
    for url in (GOOD_URL, "http://example.com", "https://api.example.com",
                "https://other.com", ""):
        _rejected(api, validator, url)


@pytest.mark.robustness
def test_R08_invalid_port_value(api):
    validator = _validator(api)
    for bad in BAD_PORTS:
        _rejected(api, validator, bad)


@pytest.mark.robustness
def test_R09_ipv6_url_not_allowed(api):
    validator = _validator(api)
    for url in ("https://[2001:4860:4860::8888]",
                "https://[2001:4860:4860::8888]:443/",
                "https://[2606:4700:4700::1111]/dns"):
        _rejected(api, validator, url)


@pytest.mark.robustness
def test_R10_very_long_malformed_url(api):
    validator = _validator(api)
    for url in ("https://" + "a" * 10000 + " " + "b" * 10000,
                "https://" + "a." * 5000 + "evil.com",
                "https://example.com:" + "9" * 5000 + "/",
                "ht" + "t" * 20000 + "p://example.com"):
        _rejected(api, validator, url)


@pytest.mark.robustness
def test_R11_whitespace_around_url(api):
    """Trimming a wrapped URL and rejecting it as malformed are both defensible
    policies, so neither verdict is required for a URL that is otherwise valid.
    Two things are:

    * whitespace never turns a rejected URL into an accepted one - the "without
      bypassing validation" half of the design table, and the only half with
      security consequences;
    * the same kind of whitespace is handled the same way regardless of how
      much of it there is.

    Agreement ACROSS kinds of whitespace is deliberately not asserted, because
    `urlsplit` itself does not have it: it strips tab, CR and LF from anywhere
    in the URL but leaves spaces in place, so `"\\thttps://x\\n"` parses while
    `" https://x "` does not. Requiring agreement would score that stdlib
    quirk instead of the solution."""
    validator = _validator(api)
    for pair in ((f" {GOOD_URL} ", f"   {GOOD_URL}   "),
                 (f"{GOOD_URL} ", f"{GOOD_URL}   "),
                 (f"\t{GOOD_URL}\t", f"\t\t{GOOD_URL}\t\t"),
                 (f"\n{GOOD_URL}\n", f"\n\n{GOOD_URL}\n\n")):
        one, many = (bool(_check(api, validator, f)) for f in pair)
        assert one == many, (
            f"same whitespace, different amount, different verdict: "
            f"{pair[0]!r} -> {one}, {pair[1]!r} -> {many}")

    for blank in ("", "   ", "\t", "\n", " \r\n "):
        _rejected(api, validator, blank)

    for bad in ("https://other.com", "ftp://example.com",
                "https://example.com:8080", "https://sub.example.com",
                "https://evil.com@example.com"):
        for form in (f" {bad} ", f"{bad}\n", f"\t{bad}", f"  {bad}  "):
            _rejected(api, validator, form)


@pytest.mark.robustness
def test_R12_mixed_case_hostname_and_scheme(api):
    """Both sides are folded, not just the URL. urlsplit already lowercases the
    scheme and the hostname it returns, so a mixed-case URL alone proves
    nothing; the configured lists are mixed-case here, so this passes only when
    the solution folds allowed_schemes and allowed_hosts too."""
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
def test_S08_private_192_168(api):
    _rejected_even_if_allowed(api, PRIVATE_192)


@pytest.mark.security
def test_S09_private_10(api):
    _rejected_even_if_allowed(api, PRIVATE_10)


@pytest.mark.security
def test_S10_private_172_16(api):
    _rejected_even_if_allowed(api, PRIVATE_172)


@pytest.mark.security
def test_S11_link_local_metadata_address(api):
    _rejected_even_if_allowed(api, LINK_LOCAL)


@pytest.mark.security
def test_S12_loopback_ipv6(api):
    _rejected_even_if_allowed(api, LOOPBACK_V6)


@pytest.mark.security
def test_S13_ip_in_blocked_networks(api):
    """The only reason to reject these is blocked_networks: none of them is
    private, loopback, link-local, reserved or multicast."""
    for host in IN_BLOCKED_NETWORK:
        _rejected_even_if_allowed(api, host)
        _rejected(api, _validator(api, hosts=list(ALLOWED_HOSTS) + [host]),
                  _url(host, scheme="http", port=443))


@pytest.mark.security
def test_S14_allowed_host_only_as_substring(api):
    validator = _validator(api)
    for host in CONFUSABLE_HOSTS:
        _rejected(api, validator, _url(host))
        _rejected(api, validator, _url(host, path="/path"))


@pytest.mark.security
def test_S16_deny_by_default(api):
    """Anything the validator cannot parse into an unambiguously allowed
    scheme, host and port is rejected, not accepted and not raised."""
    validator = _validator(api)
    for url in UNCERTAIN:
        _rejected(api, validator, url)
