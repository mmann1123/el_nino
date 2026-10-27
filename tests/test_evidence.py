"""Every labeled drought year in config traces to evidence in
experiments/evidence/labels.csv, with a verdict that matches the label."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import pytest

from el_nino import config

LABELS_CSV = Path(__file__).resolve().parents[1] / "experiments" / "evidence" / "labels.csv"
# Seasons whose labels predate the evidence pass.
PENDING: set[tuple[str, str]] = set()


def _evidence() -> dict[tuple[str, str, int], set[str]]:
    out: dict[tuple[str, str, int], set[str]] = defaultdict(set)
    with LABELS_CSV.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["verdict"] == "drought" and row["grade"] not in ("A", "B"):
                continue
            out[(row["country"], row["season"], int(row["year"]))].add(row["verdict"])
    return out


CASES = [
    (cc["short_code"].lower(), s["key"], year, sev)
    for cc in config.COUNTRIES.values()
    for s in cc["seasons"]
    if (cc["short_code"].lower(), s["key"]) not in PENDING
    for year, (sev, _) in s["labeled_events"].items()
]


@pytest.mark.parametrize("country, season, year, severity", CASES)
def test_label_matches_evidence(country, season, year, severity):
    verdicts = _evidence().get((country, season, year), set())
    if severity == "normal":
        assert "normal" in verdicts
    elif severity == "excluded":
        assert verdicts & {"hurricane", "other", "drought"}, verdicts
    else:
        assert "drought" in verdicts


def test_every_copied_source_has_a_highlighted_file():
    with LABELS_CSV.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        if row["file"]:
            assert (LABELS_CSV.parent / row["file"]).exists(), row["file"]
