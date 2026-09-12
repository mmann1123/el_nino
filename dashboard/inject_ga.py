"""Inject the Google Analytics (GA4) gtag snippet into Streamlit's served HTML.

Why not just render the tag from the app? Streamlit strips `<script>` out of
`st.markdown(..., unsafe_allow_html=True)`, and `st.components.v1.html` renders
inside a sandboxed iframe whose URL is not the dashboard's — GA would report the
iframe, not the page, and its cookies are third-party. The only place a
page-level tag can run in the top frame is Streamlit's own
`static/index.html`, which the server hands to the browser before any app code
runs.

That file is served straight off disk on every cold request, so it must be
patched *before* `streamlit run` starts — not at app import time, when the first
visitor has already been served the unpatched page. Run it from the container's
CMD:

    python -m el_nino.dashboard.inject_ga && exec streamlit run ...

No-op (exit 0) when ``GA_MEASUREMENT_ID`` is unset — local dev and the ETL Job
are untracked. Re-runs are idempotent, and every failure mode is swallowed:
analytics must never be the reason a container refuses to boot.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

# Sentinel comment so a re-run (or a warm container restart) does not stack a
# second copy of the tag into the same file.
MARKER = "<!-- el_nino google analytics -->"

# GA4 measurement IDs look like G-XXXXXXXXXX. Validated because the value lands
# inside a quoted JS string literal in the page we write.
_ID_RE = re.compile(r"^G-[A-Z0-9]+$")


def snippet(measurement_id: str) -> str:
    """Return the standard gtag.js snippet for ``measurement_id``."""
    return (
        f"{MARKER}\n"
        f'<script async src="https://www.googletagmanager.com/gtag/js?'
        f'id={measurement_id}"></script>\n'
        "<script>\n"
        "  window.dataLayer = window.dataLayer || [];\n"
        "  function gtag(){dataLayer.push(arguments);}\n"
        "  gtag('js', new Date());\n"
        f"  gtag('config', '{measurement_id}');\n"
        "</script>\n"
    )


def patch_html(html: str, measurement_id: str) -> str:
    """Return ``html`` with the gtag snippet inserted just inside ``<head>``.

    Returns the input unchanged if it is already patched or has no ``<head>``.
    """
    if MARKER in html or "<head>" not in html:
        return html
    return html.replace("<head>", "<head>\n" + snippet(measurement_id), 1)


def streamlit_index() -> Path:
    """Path to the `index.html` Streamlit serves for the app shell."""
    import streamlit

    return Path(streamlit.__file__).resolve().parent / "static" / "index.html"


def main() -> int:
    measurement_id = os.environ.get("GA_MEASUREMENT_ID", "").strip()
    if not measurement_id:
        print("inject_ga: GA_MEASUREMENT_ID unset — analytics disabled.")
        return 0
    if not _ID_RE.match(measurement_id):
        print(
            f"inject_ga: ignoring malformed GA_MEASUREMENT_ID "
            f"{measurement_id!r} (expected G-XXXXXXXXXX).",
            file=sys.stderr,
        )
        return 0

    try:
        index = streamlit_index()
        html = index.read_text(encoding="utf-8")
        patched = patch_html(html, measurement_id)
        if patched == html:
            print("inject_ga: already patched (or no <head>) — nothing to do.")
            return 0
        index.write_text(patched, encoding="utf-8")
    except Exception as exc:  # never block container startup on analytics
        print(f"inject_ga: skipped ({type(exc).__name__}: {exc})", file=sys.stderr)
        return 0

    print(f"inject_ga: tagged {index} with {measurement_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
