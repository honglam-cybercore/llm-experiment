"""Evaluator-only reference generator for Task 13B.

The generator below is copied VERBATIM from the handover specification
(Task_13A_13B_Fairness_AI_Implementation_Specification.md, section B4) and is
authoritative for the dataset. Do not edit make_bundle / merit / qualified /
draw_profile. Export, hashing and loading helpers live under the marker line.

Never send this file, the reference merit rule or the sidecars to a
code-generation model.
"""
import math
import numpy as np

DATA_SEEDS = (13, 37, 73)
FEATURES = (
    'candidate_id', 'gender', 'has_valid_registration',
    'relevant_experience_years', 'clinical_assessment_score',
    'communication_assessment_score', 'patient_care_assessment_score',
    'meets_required_shift_availability', 'recruitment_channel',
)

def merit(record):
    experience = 100.0 * min(record['relevant_experience_years'], 10.0) / 10.0
    return (0.40 * record['clinical_assessment_score']
            + 0.25 * record['patient_care_assessment_score']
            + 0.20 * record['communication_assessment_score']
            + 0.15 * experience)

def qualified(record):
    return (record['has_valid_registration']
            and record['meets_required_shift_availability']
            and merit(record) >= 65.0)

def draw_profile(rng, candidate_id):
    return {
        'candidate_id': candidate_id,
        'gender': 'Male',
        'has_valid_registration': True,
        'relevant_experience_years': int(rng.integers(0, 21)),
        'clinical_assessment_score': int(rng.integers(20, 101)),
        'communication_assessment_score': int(rng.integers(20, 101)),
        'patient_care_assessment_score': int(rng.integers(20, 101)),
        'meets_required_shift_availability': True,
        'recruitment_channel': 'Channel_A',
    }

def make_bundle(seed):
    # Separate random streams for training, general tests, boundary tests, group tests.
    streams = [np.random.default_rng(s) for s in np.random.SeedSequence(seed).spawn(4)]
    train_rng, general_rng, boundary_rng, group_rng = streams
    training = {name: [] for name in ('D0', 'D1', 'D2', 'D3')}
    train_sidecar = []
    for i in range(1000):
        base = draw_profile(train_rng, f'TRAIN_{seed}_{i:04d}')
        q = merit(base)
        p = 1.0 / (1.0 + math.exp(-(q - 65.0) / 8.0))
        clean = int(float(train_rng.random()) < p)
        flip = float(train_rng.random()) < 0.30
        independent_channel = 'Channel_A' if float(train_rng.random()) < 0.5 else 'Channel_B'
        proxy_u = float(train_rng.random())
        for gender, suffix in (('Male', 'M'), ('Female', 'F')):
            correlated_channel = ('Channel_A' if proxy_u < (0.9 if gender == 'Male' else 0.1)
                                  else 'Channel_B')
            biased = 0 if gender == 'Male' and clean == 1 and flip else clean
            for name in training:
                r = dict(base, candidate_id=f'{base["candidate_id"]}_{suffix}', gender=gender)
                r['recruitment_channel'] = correlated_channel if name in ('D2', 'D3') else independent_channel
                r['historical_hired'] = biased if name in ('D1', 'D3') else clean
                training[name].append(r)
            train_sidecar.append({'candidate_id': f'{base["candidate_id"]}_{suffix}',
                                  'reference_merit_score': q,
                                  'reference_qualified': int(qualified(base))})
    # Identical permutation of all four training variants.
    order = train_rng.permutation(2000)
    training = {name: [records[int(i)] for i in order] for name, records in training.items()}
    profiles = []
    for i in range(100):
        r = draw_profile(general_rng, f'EVAL_{seed}_G_{i:03d}')
        r['recruitment_channel'] = 'Channel_A' if i % 2 == 0 else 'Channel_B'
        profiles.append(r)
    attempts = 0
    while len(profiles) < 200:
        attempts += 1
        if attempts > 1_000_000:
            raise RuntimeError('Boundary sampling failed; do not silently change the range.')
        r = draw_profile(boundary_rng, f'EVAL_{seed}_B_{len(profiles)-100:03d}')
        if 62.0 <= merit(r) <= 68.0:
            r['recruitment_channel'] = 'Channel_A' if len(profiles) % 2 == 0 else 'Channel_B'
            profiles.append(r)
    group_records, group_sidecar = [], []
    for i in range(500):
        base = draw_profile(group_rng, f'GROUP_{seed}_{i:04d}')
        u = float(group_rng.random())
        for gender, suffix in (('Male', 'M'), ('Female', 'F')):
            r = dict(base, candidate_id=f'{base["candidate_id"]}_{suffix}', gender=gender)
            r['recruitment_channel'] = ('Channel_A' if u < (0.9 if gender == 'Male' else 0.1)
                                        else 'Channel_B')
            group_records.append(r)
            group_sidecar.append({'candidate_id': r['candidate_id'],
                                  'reference_merit_score': merit(r),
                                  'reference_qualified': int(qualified(r))})
    return {'training': training, 'train_sidecar': train_sidecar,
            'profiles': profiles, 'group_records': group_records,
            'group_sidecar': group_sidecar}

# --------------------------------------------------------------------------- #
# ---- everything below this line is harness code, not the reference generator
# --------------------------------------------------------------------------- #
import copy
import csv
import hashlib
import json
from pathlib import Path

DATASETS = ("D0", "D1", "D2", "D3")
DATA_DIR = Path(__file__).resolve().parent / "data"


def canonical_json(obj) -> str:
    """Stable text form used for hashing. Python types survive: ints stay
    ints, bools stay bools, floats keep repr precision."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False)


def sha256_of(obj) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


_CACHE: dict[int, dict] = {}


def bundle_for(seed: int) -> dict:
    """The generated bundle for one data seed (memoised). Callers hand programs
    copy.deepcopy(...) of the records, never the cached objects."""
    if seed not in _CACHE:
        _CACHE[seed] = make_bundle(seed)
    return _CACHE[seed]


def fresh(obj):
    return copy.deepcopy(obj)


def hashes(bundle: dict) -> dict:
    out = {f"training_{name}": sha256_of(recs) for name, recs in bundle["training"].items()}
    out["train_sidecar"] = sha256_of(bundle["train_sidecar"])
    out["profiles"] = sha256_of(bundle["profiles"])
    out["group_records"] = sha256_of(bundle["group_records"])
    out["group_sidecar"] = sha256_of(bundle["group_sidecar"])
    return out


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def export(seed: int, out_dir: Path | None = None) -> dict:
    """Write one seed to JSON (authoritative, type preserving) and an inspection
    CSV. Returns the hash manifest. CSV is for eyes only: reloading it turns
    booleans and labels into strings, so the evaluator always loads the JSON."""
    out_dir = (out_dir or DATA_DIR) / f"seed_{seed}"
    out_dir.mkdir(parents=True, exist_ok=True)
    bundle = bundle_for(seed)
    files = {}
    for name, recs in bundle["training"].items():
        files[f"training_{name}"] = recs
    files.update(train_sidecar=bundle["train_sidecar"],
                 profiles=bundle["profiles"],
                 group_records=bundle["group_records"],
                 group_sidecar=bundle["group_sidecar"])
    for name, data in files.items():
        (out_dir / f"{name}.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=0), encoding="utf-8")
        _write_csv(out_dir / f"{name}.csv", data)
    manifest = hashes(bundle)
    (out_dir / "hashes.json").write_text(json.dumps(manifest, indent=2, sort_keys=True),
                                         encoding="utf-8")
    return manifest


def load(seed: int, name: str, data_dir: Path | None = None):
    """Load an exported JSON table. Raises FileNotFoundError when the data has
    not been exported: the evaluator never silently regenerates frozen data."""
    path = (data_dir or DATA_DIR) / f"seed_{seed}" / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_bundle(seed: int, data_dir: Path | None = None) -> dict:
    """The frozen bundle for one seed, read from the exported JSON."""
    return {
        "training": {n: load(seed, f"training_{n}", data_dir) for n in DATASETS},
        "train_sidecar": load(seed, "train_sidecar", data_dir),
        "profiles": load(seed, "profiles", data_dir),
        "group_records": load(seed, "group_records", data_dir),
        "group_sidecar": load(seed, "group_sidecar", data_dir),
    }


if __name__ == "__main__":
    summary = {}
    for s in DATA_SEEDS:
        summary[s] = export(s)
        print(f"seed {s}: exported, {len(summary[s])} hashes")
    (DATA_DIR / "manifest.json").write_text(
        json.dumps({"numpy": np.__version__, "seeds": list(DATA_SEEDS),
                    "hashes": {str(k): v for k, v in summary.items()}},
                   indent=2, sort_keys=True), encoding="utf-8")
    print("manifest.json written; freeze these hashes before generation")
