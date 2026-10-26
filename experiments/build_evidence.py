"""Download and highlight the sources behind every drought label.

Reads experiments/evidence/labels.csv (one row per piece of evidence), saves
each government/UN source as a PDF in experiments/evidence/ with the quoted
passage highlighted, and writes the output file and page back into the CSV.
News sources are never copied: their rows keep only the URL and quote.

HTML pages are rendered to PDF with headless Chrome first, so every source is
highlighted the same way. Only the highlighted pages are kept, stamped with
their original page number and URL and saved as page images (rendered web
pages embed large maps; the quote text itself is in labels.csv). The `page`
column always refers to the original document. A quote that can't be found is reported and the run
exits non-zero: every label must trace to highlighted text.

Run from the parent directory (needs `pip install pymupdf`, kept out of
requirements.txt so it stays out of the Cloud Run image):
    python -m el_nino.experiments.build_evidence
"""

from __future__ import annotations

import csv
import hashlib
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pymupdf
import requests

EVIDENCE_DIR = Path(__file__).parent / "evidence"
LABELS = EVIDENCE_DIR / "labels.csv"
CACHE = EVIDENCE_DIR / ".cache"     # raw downloads, gitignored; delete to re-fetch
FIELDS = ["country", "season", "year", "grade", "verdict", "departments",
          "quote", "source", "date", "url", "file", "page"]

# Public-domain or openly licensed publishers whose documents we keep copies of.
COPYABLE = ("FEWS NET", "FAO", "GIEWS", "WFP", "UNICEF", "NOAA", "CPC", "USDA", "MAG", "CNSA")
SNAPSHOT_DPI = 120
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"}


def _copyable(source: str) -> bool:
    return any(p.lower() in source.lower() for p in COPYABLE)


def _slug(group: list[dict]) -> str:
    """File stem for one source document: country (or "multi"), publisher and
    report date, or "archive" for a multi-report archive like GIEWS'."""
    first = group[0]
    src = re.sub(r"[^a-z0-9]+", "-", first["source"].lower()).strip("-")
    country = first["country"] if len({r["country"] for r in group}) == 1 else "multi"
    when = first["date"] if len({r["date"] for r in group}) == 1 else "archive"
    return f"{country}_{src}_{when}"


def _chrome() -> str:
    for name in ("google-chrome", "chromium", "chromium-browser"):
        if path := shutil.which(name):
            return path
    raise SystemExit("headless Chrome is needed to render HTML sources")


def _fetch_pdf(url: str) -> Path:
    """`url` as a PDF in the download cache, rendering HTML through Chrome.
    Backs off and retries when the site rate-limits (HTTP 429)."""
    CACHE.mkdir(exist_ok=True)
    out = CACHE / f"{hashlib.sha1(url.encode()).hexdigest()[:16]}.pdf"
    if out.exists():
        return out
    for wait in (30, 90, 0):
        r = requests.get(url, headers=UA, timeout=60)
        if r.status_code != 429 or not wait:
            break
        time.sleep(wait)
    r.raise_for_status()
    if r.content[:4] == b"%PDF":
        out.write_bytes(r.content)
        return out
    subprocess.run(
        [_chrome(), "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
         "--virtual-time-budget=15000", f"--print-to-pdf={out}", url],
        check=True, capture_output=True, timeout=120,
    )
    return out


def _find(doc: pymupdf.Document, quote: str, page_hint: str) -> tuple[int, list] | None:
    """(1-based page, hit rects) for `quote`, trying the hinted page first.
    Falls back to the quote's first or last eight words when a line break or
    page overlay (e.g. a cookie banner) splits it."""
    pages = list(range(len(doc)))
    if page_hint.isdigit() and 0 < int(page_hint) <= len(doc):
        pages.insert(0, pages.pop(int(page_hint) - 1))
    words = quote.split()
    for needle in (quote, " ".join(words[:8]), " ".join(words[-8:])):
        for i in pages:
            if hits := doc[i].search_for(needle):
                return i + 1, hits
    return None


def _snapshot(doc: pymupdf.Document, url: str, cited: set[int]) -> pymupdf.Document:
    """The cited pages, stamped with where they came from, as page images."""
    out = pymupdf.open()
    for n in sorted(cited):
        page = doc[n - 1]
        page.insert_text((24, 14), f"Original page {n} of {len(doc)} — {url}",
                         fontsize=7, color=(0.4, 0.4, 0.4))
        pix = page.get_pixmap(dpi=SNAPSHOT_DPI, annots=True)
        img = out.new_page(width=page.rect.width, height=page.rect.height)
        img.insert_image(img.rect, stream=pix.tobytes("jpeg", jpg_quality=70))
    return out


def main() -> int:
    with LABELS.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    by_url: dict[str, list[dict]] = {}
    for row in rows:
        if _copyable(row["source"]):
            by_url.setdefault(row["url"], []).append(row)
        else:
            row["file"], row["page"] = "", ""

    missing = []
    for url, group in by_url.items():
        try:
            raw = _fetch_pdf(url)
        except Exception as exc:  # noqa: BLE001 — report every failure, keep going
            missing.extend((r, f"download failed: {exc}") for r in group)
            continue
        doc = pymupdf.open(raw)
        for row in group:
            found = _find(doc, row["quote"], row.get("page", ""))
            if found is None:
                missing.append((row, "quote not found"))
                continue
            page, hits = found
            for rect in hits:
                doc[page - 1].add_highlight_annot(rect)
            row["page"] = str(page)
        cited = {int(r["page"]) for r in group if r.get("page", "").isdigit()}
        name = f"{_slug(group)}.pdf"
        _snapshot(doc, url, cited).save(EVIDENCE_DIR / name, garbage=4, deflate=True)
        for row in group:
            row["file"] = name

    with LABELS.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    for row, why in missing:
        print(f"MISSING {row['country']} {row['season']} {row['year']} "
              f"{row['source']}: {why}\n    {row['url']}", file=sys.stderr)
    print(f"{len(rows) - len(missing)}/{len(rows)} labels traced to highlighted text")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
