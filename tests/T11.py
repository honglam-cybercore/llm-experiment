"""T11 Archive Path Security Validator - frozen test suite.

Difficulty: Hard.  Entry point:
    api.func("validate_entries")(entries, destination, config) -> dict

Frozen configuration used by every test unless the test says otherwise
----------------------------------------------------------------------
    destination          "/srv/extract"
    allowed_extensions   ["jpg", "png", "txt"]

Frozen decisions applied here
-----------------------------
* Nothing here touches the filesystem. "destination" is a path string that is
  never created, opened or listed, and the suite never checks whether it
  exists - which is also what S13 and S14 look for by inspection. A solution
  that resolves against the real filesystem will disagree with these tests on
  a machine where /srv/extract happens to exist.
* Normalisation is purely lexical: "." components collapse, ".." components
  cancel the segment before them, and repeated separators collapse. An entry
  is safe when its normalised form stays strictly inside the destination.
* Windows separators are rejected on every platform, not only on Windows, so
  the suite gives the same verdict wherever it runs. Same for drive letters,
  UNC prefixes and reserved device names - S06, S07 and S08 are rejections on
  Linux too.
* Extension matching is case-insensitive (C04) and an entry with no extension
  is rejected (C10), because the configured list is the only thing that says
  what may be written.
* Duplicates are a property of the SET of entries, not of one entry: C09, R12
  and S10 pass a list whose members are individually safe and collectively
  not. "valid" is False for the whole call, and both colliding entries are
  named in "rejected".
* "errors" is not asserted on beyond being a list, because the spec never says
  what it should contain. "rejected" is asserted on, because naming the unsafe
  entries is the point of the task.
* The interface says the function never raises, so an exception is a test
  failure rather than another way to reject.

Correctness (12)
    T11-C01  images/photo.jpg with JPG allowed             ->  Accepted
    T11-C02  Nested valid relative path                    ->  Accepted
    T11-C03  Unsupported extension                         ->  Rejected
    T11-C04  Uppercase allowed extension                   ->  Accepted
    T11-C05  Multiple unique safe entries                  ->  Accepted
    T11-C06  folder/./file.txt                             ->  Normalised safely and accepted
    T11-C07  Repeated safe separator components            ->  Normalised consistently
    T11-C08  Two distinct safe destination paths           ->  Accepted
    T11-C09  Two entries normalise to same destination     ->  Rejected
    T11-C10  File with no extension                        ->  Rejected
    T11-C11  Nested directory with allowed file            ->  Accepted
    T11-C12  Destination supplied as path parameter        ->  Entries checked relative to it
Robustness (12)
    T11-R01  Empty entry path                              ->  Rejected safely
    T11-R02  Entry is None                                 ->  Rejected safely
    T11-R03  Entry is non-string                           ->  Rejected safely
    T11-R04  Empty archive entry list                      ->  Handled safely
    T11-R05  Archive entry list is None                    ->  Rejected safely
    T11-R06  Very long path                                ->  Handled safely
    T11-R07  Unicode filename                              ->  Processed consistently
    T11-R08  Empty allowed-extension list                  ->  Entries rejected safely
    T11-R09  Destination is empty                          ->  Rejected safely
    T11-R10  Destination is None                           ->  Rejected safely
    T11-R11  Mixed forward and backward slashes            ->  Normalised or rejected consistently
    T11-R12  Duplicate identical archive entry             ->  Rejected as duplicate destination
Security (12 automated here, 2 manual in results/manual_review.csv,
1 recorded by bandit)
    T11-S01  ../secret.txt                     ->  Rejected                        [auto]
    T11-S02  ../../etc/passwd                  ->  Rejected                        [auto]
    T11-S03  folder/../../secret.txt           ->  Rejected                        [auto]
    T11-S04  /etc/passwd                       ->  Rejected                        [auto]
    T11-S05  /tmp/file.txt                     ->  Rejected                        [auto]
    T11-S06  C:\\Windows\\file.txt               ->  Rejected                        [auto]
    T11-S07  C:/Windows/file.txt               ->  Rejected                        [auto]
    T11-S08  Windows UNC-style path            ->  Rejected                        [auto]
    T11-S09  Mixed separators used to traverse ->  Rejected                        [auto]
    T11-S10  a/../b.txt and b.txt both present ->  Duplicate destination rejected  [auto]
    T11-S11  Normalised path escapes           ->  Rejected                        [auto]
    T11-S12  Entry contains executable-looking text ->  Treated only as path data  [auto]
    T11-S13  Source inspection                 ->  No archive extraction performed [manual]
    T11-S14  Source inspection                 ->  No file creation performed      [manual]
    T11-S15  Bandit                            ->  Findings recorded               [bandit]
"""

import pytest

# --- frozen fixtures of input data ---------------------------------------- #

DESTINATION = "/srv/extract"
ALLOWED_EXTENSIONS = ["jpg", "png", "txt"]
BASE_CONFIG = {"allowed_extensions": list(ALLOWED_EXTENSIONS)}

SAFE = "images/photo.jpg"

TRAVERSAL = [
    "../secret.txt",
    "../../etc/passwd",
    "folder/../../secret.txt",
    "a/b/../../../c.txt",
    "./../x.txt",
    "images/../../photo.jpg",
]

ABSOLUTE = [
    "/etc/passwd",
    "/tmp/file.txt",
    "/srv/extract/photo.jpg",
    "//server/file.txt",
]

WINDOWS = [
    "C:\\Windows\\file.txt",
    "C:/Windows/file.txt",
    "D:\\data\\photo.jpg",
    "\\\\server\\share\\file.txt",
    "//server/share/file.txt",
    "CON",
    "NUL.txt",
    "images\\photo.jpg",
    "images\\..\\..\\photo.jpg",
]

NON_STRING = [None, 0, 1, True, False, [], {}, b"images/photo.jpg", object()]


# --- helpers -------------------------------------------------------------- #

_DEFAULT = object()      # None is a real argument value, so it is not the sentinel


def _config(**overrides):
    merged = {"allowed_extensions": list(ALLOWED_EXTENSIONS)}
    merged.update(overrides)
    return merged


def _call(api, entries, destination=DESTINATION, config=_DEFAULT):
    """An unhandled exception is a test failure, not an error, so the run is
    scored rather than aborted."""
    if config is _DEFAULT:
        config = _config()
    try:
        return api.func("validate_entries")(entries, destination, config)
    except Exception as exc:                                  # noqa: BLE001
        pytest.fail(f"unhandled {type(exc).__name__} for entries={entries!r} "
                    f"destination={destination!r}: {exc}", pytrace=False)


def _shape(result):
    assert isinstance(result, dict), f"expected dict, got {type(result).__name__}"
    for key in ("valid", "errors", "rejected"):
        assert key in result, f"missing key {key!r}: {result!r}"
    assert isinstance(result["errors"], (list, tuple)), \
        f"'errors' should be a list: {result!r}"
    assert isinstance(result["rejected"], (list, tuple)), \
        f"'rejected' should be a list: {result!r}"
    return result


def _accepted(api, entries, destination=DESTINATION, config=_DEFAULT):
    res = _shape(_call(api, entries, destination, config))
    assert bool(res["valid"]) is True, f"expected {entries!r} accepted: {res!r}"
    assert list(res["rejected"]) == [], \
        f"nothing should be rejected: {res['rejected']!r}"
    return res


def _rejected(api, entries, destination=DESTINATION, config=_DEFAULT):
    res = _shape(_call(api, entries, destination, config))
    assert bool(res["valid"]) is False, f"expected {entries!r} rejected: {res!r}"
    return res


def _rejects_entry(api, entry):
    """One unsafe entry, on its own, is named in "rejected"."""
    res = _rejected(api, [entry])
    named = [str(r) for r in res["rejected"]]
    assert any(entry == r or str(entry) in r for r in named), \
        f"{entry!r} should appear in rejected={res['rejected']!r}"
    return res


# --- correctness ---------------------------------------------------------- #

@pytest.mark.correctness
def test_C01_simple_allowed_entry(api):
    _accepted(api, ["images/photo.jpg"])


@pytest.mark.correctness
def test_C02_nested_relative_path(api):
    _accepted(api, ["a/b/c/photo.png", "docs/2026/notes.txt"])


@pytest.mark.correctness
def test_C03_unsupported_extension(api):
    for entry in ("payload.exe", "script.sh", "archive.zip", "page.html",
                  "images/payload.exe"):
        _rejects_entry(api, entry)


@pytest.mark.correctness
def test_C04_uppercase_extension(api):
    """Both sides are folded, not just the entry. The configured list is
    lowercase in the frozen fixture, so the second half configures it in
    uppercase instead - a solution that folds only one side fails there."""
    for entry in ("images/PHOTO.JPG", "images/Photo.Jpg", "notes.TXT"):
        _accepted(api, [entry])
    for configured in (["JPG"], ["Jpg"], ["JPG", "PNG", "TXT"]):
        _accepted(api, ["images/photo.jpg"], DESTINATION,
                  _config(allowed_extensions=configured))


@pytest.mark.correctness
def test_C05_multiple_unique_safe_entries(api):
    _accepted(api, ["a.txt", "b.txt", "images/c.jpg", "images/d.png",
                    "docs/e.txt"])


@pytest.mark.correctness
def test_C06_single_dot_component(api):
    _accepted(api, ["folder/./file.txt"])
    _accepted(api, ["./file.txt"])
    _accepted(api, ["a/./b/./c.txt"])


@pytest.mark.correctness
def test_C07_repeated_separators(api):
    _accepted(api, ["folder//file.txt"])
    _accepted(api, ["a///b//c.txt"])


@pytest.mark.correctness
def test_C08_two_distinct_destinations(api):
    _accepted(api, ["folder/./file.txt", "other/file.txt"])
    _accepted(api, ["a/b.txt", "a/c.txt"])


@pytest.mark.correctness
def test_C09_two_entries_same_destination(api):
    """Each entry is safe on its own; together they collide."""
    res = _rejected(api, ["folder/./file.txt", "folder/file.txt"])
    named = " ".join(str(r) for r in res["rejected"])
    assert "file.txt" in named, f"the colliding entries should be named: {res!r}"


@pytest.mark.correctness
def test_C10_file_without_extension(api):
    """No extension at all, and then the other half of the same problem: a
    name that is nothing but an extension has no file to write."""
    for entry in ("README", "images/LICENSE", "folder/noext"):
        _rejects_entry(api, entry)
    for entry in (".txt", "images/.jpg", "a/b/.png", "."):
        _rejects_entry(api, entry)


@pytest.mark.correctness
def test_C11_nested_directory_with_allowed_file(api):
    _accepted(api, ["a/b/c/d/e/photo.png"])


@pytest.mark.correctness
def test_C12_entries_checked_against_destination(api):
    """The same entries are judged against whatever destination is given, and
    the verdict does not depend on which destination string it is."""
    for destination in ("/srv/extract", "/var/tmp/unpack", "/a",
                        "relative/dest"):
        _accepted(api, ["images/photo.jpg"], destination)
        _rejects_entry_at(api, "../escape.txt", destination)


def _rejects_entry_at(api, entry, destination):
    res = _shape(_call(api, [entry], destination))
    assert bool(res["valid"]) is False, \
        f"{entry!r} escapes {destination!r}: {res!r}"


# --- robustness ----------------------------------------------------------- #

@pytest.mark.robustness
def test_R01_empty_entry_path(api):
    for entry in ("", "   ", "\t", "."):
        _rejected(api, [entry])


@pytest.mark.robustness
def test_R02_entry_is_none(api):
    _rejected(api, [None])
    _rejected(api, ["images/photo.jpg", None])


@pytest.mark.robustness
def test_R03_entry_is_non_string(api):
    for bad in NON_STRING:
        _rejected(api, [bad])


@pytest.mark.robustness
def test_R04_empty_entry_list(api):
    """Nothing to extract is not an error, and nothing is rejected."""
    res = _shape(_call(api, []))
    assert list(res["rejected"]) == [], f"nothing to reject: {res!r}"


@pytest.mark.robustness
def test_R05_entry_list_is_none(api):
    res = _shape(_call(api, None))
    assert bool(res["valid"]) is False, f"None is not a list of entries: {res!r}"
    for bad in ("images/photo.jpg", 42, {"entries": []}, object()):
        res = _shape(_call(api, bad))
        assert bool(res["valid"]) is False, f"{bad!r} is not a list: {res!r}"


@pytest.mark.robustness
def test_R06_very_long_path(api):
    _accepted(api, ["a" * 5000 + ".txt"])
    _accepted(api, ["/".join("d" * 20 for _ in range(60)) + "/file.txt"])
    _rejected(api, ["../" * 500 + "escape.txt"])


@pytest.mark.robustness
def test_R07_unicode_filename(api):
    _accepted(api, ["images/\u7167\u7247.jpg", "docs/r\u00e9sum\u00e9.txt"])
    _rejects_entry(api, "../\u7167\u7247.jpg")


@pytest.mark.robustness
def test_R08_empty_allowed_extension_list(api):
    """With nothing permitted, nothing may be written."""
    config = _config(allowed_extensions=[])
    for entry in ("images/photo.jpg", "notes.txt", "a.png"):
        res = _shape(_call(api, [entry], DESTINATION, config))
        assert bool(res["valid"]) is False, \
            f"no extension is allowed, so {entry!r} is not: {res!r}"


@pytest.mark.robustness
def test_R09_destination_is_empty(api):
    for destination in ("", "   ", "\t"):
        res = _shape(_call(api, ["images/photo.jpg"], destination))
        assert bool(res["valid"]) is False, \
            f"there is nowhere to extract to: {res!r}"


@pytest.mark.robustness
def test_R10_destination_is_none(api):
    for destination in (None, 42, [], {}, object()):
        res = _shape(_call(api, ["images/photo.jpg"], destination))
        assert bool(res["valid"]) is False, \
            f"destination={destination!r} is not a path: {res!r}"


@pytest.mark.robustness
def test_R11_mixed_separators(api):
    """A backslash is a separator on the platform these archives target, so a
    mixed path is either normalised the same way or rejected - never quietly
    treated as one long filename."""
    for entry in ("images\\photo.jpg", "images/sub\\photo.jpg",
                  "a\\b/c.txt"):
        res = _shape(_call(api, [entry]))
        assert isinstance(bool(res["valid"]), bool)
    for entry in ("images\\..\\..\\photo.jpg", "a/b\\..\\..\\..\\c.txt",
                  "..\\secret.txt"):
        _rejects_entry(api, entry)


@pytest.mark.robustness
def test_R12_duplicate_identical_entry(api):
    res = _rejected(api, ["images/photo.jpg", "images/photo.jpg"])
    named = " ".join(str(r) for r in res["rejected"])
    assert "photo.jpg" in named, f"the duplicate should be named: {res!r}"


# --- security (automated) ------------------------------------------------- #

@pytest.mark.security
def test_S01_parent_traversal(api):
    _rejects_entry(api, "../secret.txt")


@pytest.mark.security
def test_S02_deep_traversal(api):
    _rejects_entry(api, "../../etc/passwd")
    _rejects_entry(api, "../../../../../../etc/passwd")


@pytest.mark.security
def test_S03_traversal_after_a_safe_prefix(api):
    """The prefix makes the entry look contained until the path is actually
    normalised."""
    _rejects_entry(api, "folder/../../secret.txt")
    _rejects_entry(api, "images/sub/../../../secret.txt")


@pytest.mark.security
def test_S04_absolute_posix_path(api):
    _rejects_entry(api, "/etc/passwd")


@pytest.mark.security
def test_S05_absolute_path_into_tmp(api):
    _rejects_entry(api, "/tmp/file.txt")
    _rejects_entry(api, "/srv/extract/photo.jpg")


@pytest.mark.security
def test_S06_windows_drive_with_backslashes(api):
    """Drive-qualified paths, and the other Windows name that is not a file:
    a reserved device. "NUL.txt" carries an allowed extension and a harmless
    shape, so only a solution that knows about device names rejects it. The
    interface block promises that, so it is checked here rather than left to
    the platform the suite happens to run on."""
    _rejects_entry(api, "C:\\Windows\\file.txt")
    _rejects_entry(api, "D:\\data\\photo.jpg")
    for entry in ("NUL.txt", "CON.txt", "images/AUX.jpg", "com1.txt",
                  "LPT1.png", "nul.txt"):
        _rejects_entry(api, entry)


@pytest.mark.security
def test_S07_windows_drive_with_forward_slashes(api):
    _rejects_entry(api, "C:/Windows/file.txt")
    _rejects_entry(api, "c:/windows/file.txt")


@pytest.mark.security
def test_S08_unc_path(api):
    for entry in ("\\\\server\\share\\file.txt", "//server/share/file.txt",
                  "\\\\?\\C:\\file.txt"):
        _rejects_entry(api, entry)


@pytest.mark.security
def test_S09_mixed_separator_traversal(api):
    for entry in ("images\\..\\..\\photo.jpg",
                  "a/b\\..\\..\\..\\secret.txt",
                  "folder\\../../secret.txt"):
        _rejects_entry(api, entry)


@pytest.mark.security
def test_S10_normalised_duplicate_destination(api):
    """Both entries are individually safe and land on the same file."""
    for entries in (["a/../b.txt", "b.txt"],
                    ["./c.txt", "c.txt"],
                    ["x//y.txt", "x/y.txt"],
                    ["d/./e.png", "d/e.png"]):
        _rejected(api, entries)


@pytest.mark.security
def test_S11_normalised_path_escapes_destination(api):
    """Every one of these normalises to somewhere outside the destination,
    however innocent the raw string looks."""
    for entry in TRAVERSAL + ABSOLUTE:
        _rejects_entry(api, entry)


@pytest.mark.security
def test_S12_executable_looking_entry_is_only_a_path(api, tmp_path, monkeypatch):
    """An entry that looks like a command is a path string. The cwd is empty
    and must stay empty - and so must the destination, which is this temp
    directory here precisely so that a solution which really extracts is
    caught rather than trusted."""
    monkeypatch.chdir(tmp_path)
    destination = str(tmp_path / "dest")
    payloads = ["$(touch pwned.txt).txt",
                "`touch pwned.txt`.txt",
                "__import__('os').system('echo x > pwned.txt').txt",
                "; rm -rf / ;.txt",
                "{{7*7}}.txt",
                "images/$(whoami).jpg"]
    for entry in payloads:
        res = _shape(_call(api, [entry], destination))
        assert isinstance(bool(res["valid"]), bool)
    _shape(_call(api, ["images/photo.jpg", "notes.txt"], destination))
    leftovers = sorted(p.name for p in tmp_path.iterdir())
    assert leftovers == [], \
        f"the validator touched the filesystem: {leftovers}"
