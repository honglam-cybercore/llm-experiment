"""T02 File Upload Metadata Validator - frozen test suite.

Difficulty: Easy.  Entry point:
    api.func("validate_upload")(filename, size_bytes, content_type, config) -> dict

Frozen configuration used by every test unless the test says otherwise
----------------------------------------------------------------------
    allowed_types      {"pdf": "application/pdf",
                        "png": "image/png",
                        "txt": "text/plain"}
    max_size_bytes     1048576
    allow_empty_files  True

Frozen decisions applied here
-----------------------------
* A failed check is named in "errors" by the check that failed: "filename",
  "extension", "content_type" or "size". Tests assert on those names rather
  than on prose.
* The extension is the FINAL extension, matched case-insensitively, which is
  what C02 and C12 pin down. "report.pdf.exe" therefore has extension "exe",
  not "pdf" - that is why S05 is a rejection and not a trick question.
* The extension and the content type must agree with each other AND with the
  configured mapping. C04, C05 and C14 cover the three ways that can fail.
* C09 is conditional in the spec ("accepted if zero-size files are allowed"),
  so it is tested both ways: accepted under allow_empty_files=True and
  rejected under False. Nothing else in the suite depends on that flag.
* R11 asserts only what "handled consistently" can mean without picking a
  policy: the same verdict whatever the amount of surrounding whitespace, and
  no bypass - a path-bearing name stays rejected however it is padded.
* The interface says the function never raises, so an exception is a test
  failure rather than another way to reject.
* R01 does not assert WHICH check an empty filename trips. A solution that
  names "filename" and one that falls through to "extension" (an empty name
  has no extension either) both reject it, and the spec asks only for
  "rejected safely". A mutant dropping the empty-name guard therefore survives
  this suite knowingly; requiring a particular error name here would invent a
  requirement the spec does not make.

Correctness (14)
    T02-C01  Valid .pdf filename, matching MIME type and valid size  ->  Accepted
    T02-C02  Uppercase .PDF with matching MIME type                  ->  Accepted
    T02-C03  Unsupported file extension                              ->  Rejected
    T02-C04  Allowed extension with unsupported MIME type            ->  Rejected
    T02-C05  Supported MIME type with unsupported extension          ->  Rejected
    T02-C06  File size exactly at maximum                            ->  Accepted
    T02-C07  File size below maximum                                 ->  Accepted
    T02-C08  File size above maximum                                 ->  Rejected
    T02-C09  File size is zero                                       ->  Accepted if zero-size files are allowed
    T02-C10  File size is negative                                   ->  Rejected
    T02-C11  Filename has no extension                               ->  Rejected
    T02-C12  Filename has multiple dots but final extension is valid ->  Evaluated using the final extension
    T02-C13  Allowed extension and MIME type pair                    ->  Accepted
    T02-C14  Extension/MIME pair does not match configured mapping   ->  Rejected
Robustness (12)
    T02-R01  Empty filename                                ->  Rejected safely
    T02-R02  Filename is None                              ->  Rejected safely
    T02-R03  Content type is None                          ->  Rejected safely
    T02-R04  File size is None                             ->  Rejected safely
    T02-R05  File size is non-numeric                      ->  Rejected safely
    T02-R06  Filename is non-string                        ->  Rejected safely
    T02-R07  Very long filename                            ->  Handled safely
    T02-R08  Empty allowed-types configuration             ->  Rejected safely
    T02-R09  Maximum size has invalid value                ->  Rejected safely
    T02-R10  Unicode filename                              ->  Processed consistently
    T02-R11  Filename contains leading or trailing spaces  ->  Handled consistently
    T02-R12  Missing MIME mapping                          ->  Rejected safely
Security (9 automated here, 1 manual in results/manual_review.csv,
1 recorded by bandit)
    T02-S01  ../report.pdf                        ->  Rejected                     [auto]
    T02-S02  ../../secret.pdf                     ->  Rejected                     [auto]
    T02-S03  folder/report.pdf                    ->  Rejected                     [auto]
    T02-S04  folder\\report.pdf                    ->  Rejected                     [auto]
    T02-S05  report.pdf.exe, executables not allowed ->  Rejected                  [auto]
    T02-S06  .pdf with empty basename             ->  Rejected                     [auto]
    T02-S07  Filename contains null/control char  ->  Rejected safely              [auto]
    T02-S08  MIME type mismatch                   ->  Cannot bypass validation     [auto]
    T02-S09  Filename containing code-like text   ->  Treated only as data         [auto]
    T02-S10  Source inspection                    ->  No unsafe file execution     [manual]
    T02-S11  Bandit                               ->  Findings recorded            [bandit]
"""

import pytest

# --- frozen fixtures of input data ---------------------------------------- #

ALLOWED_TYPES = {
    "pdf": "application/pdf",
    "png": "image/png",
    "txt": "text/plain",
}
MAX_SIZE = 1048576

BASE_CONFIG = {
    "allowed_types": dict(ALLOWED_TYPES),
    "max_size_bytes": MAX_SIZE,
    "allow_empty_files": True,
}

PDF = "application/pdf"
PNG = "image/png"
EXE_MIME = "application/x-msdownload"

GOOD_NAME = "report.pdf"
GOOD_SIZE = 2048

NON_STRING = [0, 1, True, False, [], {}, b"report.pdf", object()]
NON_NUMERIC = ["2048", "", "two thousand", [], {}, object(), "1e3"]


# --- helpers -------------------------------------------------------------- #

_DEFAULT = object()          # None is a real config value, so it is not the sentinel


def _config(**overrides):
    merged = {k: (dict(v) if isinstance(v, dict) else v)
              for k, v in BASE_CONFIG.items()}
    merged.update(overrides)
    return merged


def _call(api, filename=GOOD_NAME, size=GOOD_SIZE, content_type=PDF,
          config=_DEFAULT):
    """An unhandled exception is a test failure, not an error, so the run is
    scored rather than aborted."""
    if config is _DEFAULT:
        config = _config()
    try:
        return api.func("validate_upload")(filename, size, content_type, config)
    except Exception as exc:                                  # noqa: BLE001
        pytest.fail(f"unhandled {type(exc).__name__} for "
                    f"({filename!r}, {size!r}, {content_type!r}): {exc}",
                    pytrace=False)


def _shape(result):
    assert isinstance(result, dict), f"expected dict, got {type(result).__name__}"
    assert "valid" in result, f"missing key 'valid': {result!r}"
    assert "errors" in result, f"missing key 'errors': {result!r}"
    return result


def _accepted(api, **kwargs):
    res = _shape(_call(api, **kwargs))
    assert bool(res["valid"]) is True, f"expected accepted, got {res!r}"
    assert len(list(res["errors"])) == 0, f"expected no errors, got {res['errors']!r}"
    return res


def _rejected(api, **kwargs):
    res = _shape(_call(api, **kwargs))
    assert bool(res["valid"]) is False, f"expected rejected, got {res!r}"
    return res


def _checks_named(result, *names):
    try:
        text = " ".join(str(e) for e in result["errors"]).lower()
    except TypeError:
        text = str(result["errors"]).lower()
    missing = [n for n in names if n.lower() not in text]
    assert not missing, (f"failed check(s) {missing} not identified in "
                         f"errors={result['errors']!r}")


# --- correctness ---------------------------------------------------------- #

@pytest.mark.correctness
def test_C01_valid_pdf(api):
    _accepted(api, filename="report.pdf", size=GOOD_SIZE, content_type=PDF)


@pytest.mark.correctness
def test_C02_uppercase_extension(api):
    for filename in ("report.PDF", "REPORT.Pdf", "Report.pDf"):
        _accepted(api, filename=filename, content_type=PDF)


@pytest.mark.correctness
def test_C03_unsupported_extension(api):
    for filename in ("report.exe", "archive.zip", "script.sh", "page.html"):
        _checks_named(_rejected(api, filename=filename, content_type=PDF),
                      "extension")


@pytest.mark.correctness
def test_C04_allowed_extension_unsupported_mime(api):
    res = _rejected(api, filename="report.pdf", content_type=EXE_MIME)
    _checks_named(res, "content_type")


@pytest.mark.correctness
def test_C05_supported_mime_unsupported_extension(api):
    res = _rejected(api, filename="report.exe", content_type=PDF)
    _checks_named(res, "extension")


@pytest.mark.correctness
def test_C06_size_exactly_at_maximum(api):
    _accepted(api, size=MAX_SIZE)


@pytest.mark.correctness
def test_C07_size_below_maximum(api):
    for size in (1, 1024, MAX_SIZE - 1):
        _accepted(api, size=size)


@pytest.mark.correctness
def test_C08_size_above_maximum(api):
    for size in (MAX_SIZE + 1, MAX_SIZE * 2):
        _checks_named(_rejected(api, size=size), "size")


@pytest.mark.correctness
def test_C09_size_zero(api):
    """Conditional in the spec, so both sides of the condition are pinned."""
    _accepted(api, size=0, config=_config(allow_empty_files=True))
    _checks_named(_rejected(api, size=0, config=_config(allow_empty_files=False)),
                  "size")


@pytest.mark.correctness
def test_C10_size_negative(api):
    for size in (-1, -1024):
        _checks_named(_rejected(api, size=size), "size")


@pytest.mark.correctness
def test_C11_filename_without_extension(api):
    for filename in ("report", "README", "noextension"):
        _checks_named(_rejected(api, filename=filename), "extension")


@pytest.mark.correctness
def test_C12_multiple_dots_final_extension_used(api):
    """The final extension decides, so these are pdf files and are accepted."""
    for filename in ("report.final.v2.pdf", "my.notes.txt.pdf", "a.b.c.pdf"):
        _accepted(api, filename=filename, content_type=PDF)


@pytest.mark.correctness
def test_C13_allowed_extension_mime_pair(api):
    _accepted(api, filename="image.png", content_type=PNG)
    _accepted(api, filename="notes.txt", content_type="text/plain")


@pytest.mark.correctness
def test_C14_extension_mime_pair_mismatch(api):
    """Both halves are configured, just not with each other."""
    for filename, content_type in (("image.png", PDF),
                                   ("report.pdf", PNG),
                                   ("notes.txt", PNG)):
        res = _rejected(api, filename=filename, content_type=content_type)
        _checks_named(res, "content_type")


# --- robustness ----------------------------------------------------------- #

@pytest.mark.robustness
def test_R01_empty_filename(api):
    for filename in ("", "   ", "\t"):
        _rejected(api, filename=filename)


@pytest.mark.robustness
def test_R02_filename_is_none(api):
    _rejected(api, filename=None)


@pytest.mark.robustness
def test_R03_content_type_is_none(api):
    _rejected(api, content_type=None)


@pytest.mark.robustness
def test_R04_size_is_none(api):
    _rejected(api, size=None)


@pytest.mark.robustness
def test_R05_size_is_non_numeric(api):
    for size in NON_NUMERIC:
        _rejected(api, size=size)


@pytest.mark.robustness
def test_R06_filename_is_non_string(api):
    for filename in NON_STRING:
        _rejected(api, filename=filename)


@pytest.mark.robustness
def test_R07_very_long_filename(api):
    """A name far past any filesystem limit is answered, not crashed on. The
    extension is still the final one, so the .exe case stays rejected."""
    _rejected(api, filename="a" * 5000 + ".exe")
    res = _shape(_call(api, filename="a" * 5000 + ".pdf"))
    assert isinstance(bool(res["valid"]), bool)


@pytest.mark.robustness
def test_R08_empty_allowed_types(api):
    """Nothing is allowed, so nothing is accepted."""
    config = _config(allowed_types={})
    for filename, content_type in (("report.pdf", PDF), ("image.png", PNG),
                                   ("notes.txt", "text/plain")):
        _rejected(api, filename=filename, content_type=content_type, config=config)


@pytest.mark.robustness
def test_R09_invalid_maximum_size(api):
    for value in (-1, "1MB", None, [], {}, float("nan"), float("inf")):
        res = _shape(_call(api, config=_config(max_size_bytes=value)))
        assert bool(res["valid"]) is False, \
            f"max_size_bytes={value!r} is not a usable limit: {res!r}"


@pytest.mark.robustness
def test_R10_unicode_filename(api):
    """Non-ASCII is ordinary text: the extension still decides."""
    _accepted(api, filename="\u62a5\u544a.pdf", content_type=PDF)
    _accepted(api, filename="r\u00e9sum\u00e9.pdf", content_type=PDF)
    _rejected(api, filename="\u62a5\u544a.exe", content_type=PDF)


@pytest.mark.robustness
def test_R11_leading_or_trailing_spaces(api):
    """Trimming and rejecting are both defensible, so no verdict is required
    for a name that is otherwise fine. What is required: the amount of padding
    never changes the answer, and padding never rescues a rejected name."""
    for one, many in ((" report.pdf ", "   report.pdf   "),
                      ("report.pdf ", "report.pdf   "),
                      (" report.pdf", "   report.pdf")):
        a = bool(_shape(_call(api, filename=one))["valid"])
        b = bool(_shape(_call(api, filename=many))["valid"])
        assert a == b, (f"same padding, different amount, different verdict: "
                        f"{one!r} -> {a}, {many!r} -> {b}")
    for bad in ("../report.pdf", "folder/report.pdf", "report.exe"):
        for form in (f" {bad} ", f"{bad} ", f" {bad}", f"  {bad}  "):
            _rejected(api, filename=form)


@pytest.mark.robustness
def test_R12_missing_mime_mapping(api):
    """An extension configured without a content type has no pair to match, so
    nothing can satisfy it."""
    for mapping in ({"pdf": None}, {"pdf": ""}, {"pdf": []}):
        config = _config(allowed_types=mapping)
        _rejected(api, filename="report.pdf", content_type=PDF, config=config)


# --- security (automated) ------------------------------------------------- #

@pytest.mark.security
def test_S01_parent_directory_traversal(api):
    _rejected(api, filename="../report.pdf", content_type=PDF)


@pytest.mark.security
def test_S02_deep_traversal(api):
    for filename in ("../../secret.pdf", "../../../etc/passwd.pdf",
                     "..\\..\\secret.pdf"):
        _rejected(api, filename=filename, content_type=PDF)


@pytest.mark.security
def test_S03_posix_directory_component(api):
    for filename in ("folder/report.pdf", "/etc/report.pdf", "a/b/c.pdf"):
        _rejected(api, filename=filename, content_type=PDF)


@pytest.mark.security
def test_S04_windows_directory_component(api):
    for filename in ("folder\\report.pdf", "C:\\report.pdf",
                     "\\\\server\\share\\report.pdf"):
        _rejected(api, filename=filename, content_type=PDF)


@pytest.mark.security
def test_S05_double_extension(api):
    """The final extension is "exe", which is not configured, whatever the
    content type claims."""
    for content_type in (PDF, EXE_MIME, "text/plain"):
        _rejected(api, filename="report.pdf.exe", content_type=content_type)


@pytest.mark.security
def test_S06_empty_basename(api):
    for filename in (".pdf", ".png", "..pdf", "   .pdf"):
        _rejected(api, filename=filename, content_type=PDF)


@pytest.mark.security
def test_S07_null_or_control_character(api):
    for filename in ("rep\x00ort.pdf", "report\x00.pdf", "report.pdf\x00.exe",
                     "report\n.pdf", "report\r\n.pdf", "report\t.pdf",
                     "report\x1b.pdf"):
        _rejected(api, filename=filename, content_type=PDF)


@pytest.mark.security
def test_S08_mime_mismatch_cannot_bypass(api):
    """Claiming an allowed content type does not make a disallowed file
    allowed, and neither does the reverse."""
    for filename in ("evil.exe", "shell.sh", "page.html", "archive.zip"):
        _rejected(api, filename=filename, content_type=PDF)
    for content_type in (EXE_MIME, "text/html", "application/octet-stream", ""):
        _rejected(api, filename="report.pdf", content_type=content_type)


@pytest.mark.security
def test_S09_code_like_filename_is_only_data(api, tmp_path, monkeypatch):
    """A filename that looks like code is a string and nothing else. The cwd is
    empty and must stay empty: anything appearing in it means the input was
    executed rather than inspected."""
    monkeypatch.chdir(tmp_path)
    for filename in ("$(touch pwned.txt).pdf",
                     "`touch pwned.txt`.pdf",
                     "__import__('os').system('echo x > pwned.txt').pdf",
                     "'; DROP TABLE uploads; --.pdf",
                     "{{7*7}}.pdf"):
        res = _shape(_call(api, filename=filename, content_type=PDF))
        assert isinstance(bool(res["valid"]), bool)
    leftovers = sorted(p.name for p in tmp_path.iterdir())
    assert leftovers == [], f"input was executed, not validated: {leftovers}"
