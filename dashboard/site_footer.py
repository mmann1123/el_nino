"""Site-wide footer for the Streamlit dashboard — attribution, data sources,
disclaimer, and GWU Department of Geography & Environment mark.

The GW logo PNG lives in the repo's `static/` and is base64-embedded into the
markup at render time, so it ships with the app without depending on
Streamlit's static-serving config.

Matches the landing page's footer copy so both surfaces present the same
attribution.
"""

from __future__ import annotations

import base64
import functools
from pathlib import Path

import streamlit as st


_GWU_DEPT_URL = "https://geography.columbian.gwu.edu/"
_GWU_LOGO_PATH = Path(__file__).resolve().parents[1] / "static" / "GW_GE.png"


@functools.lru_cache(maxsize=1)
def _gwu_logo_src() -> str:
    """Return a `data:` URI for the GW logo, or empty string if the file is
    missing. Cached so we read+encode once per process."""
    if not _GWU_LOGO_PATH.exists() or _GWU_LOGO_PATH.stat().st_size == 0:
        return ""
    b64 = base64.b64encode(_GWU_LOGO_PATH.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{b64}"


_FOOTER_CSS = """
<style>
.site-footer {
  margin-top: 3rem;
  padding: 1.75rem 0 0.5rem;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
               "Helvetica Neue", Arial, system-ui, sans-serif;
  color: #3b3a36;
  font-size: 0.82rem;
  line-height: 1.55;
}
.site-footer .footer-inner {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  align-items: center;
  text-align: center;
}
@media (min-width: 768px) {
  .site-footer .footer-inner {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
    text-align: left;
    gap: 2rem;
  }
}
.site-footer .footer-text { max-width: 48rem; margin: 0; }
.site-footer .footer-text a {
  color: #1a4a6e;
  text-decoration: underline;
  text-decoration-color: rgba(26, 74, 110, 0.35);
  text-underline-offset: 2px;
  transition: text-decoration-color 0.15s;
}
.site-footer .footer-text a:hover { text-decoration-color: #1a4a6e; }
.site-footer .gwu-mark { display: block; flex-shrink: 0; }
.site-footer .gwu-mark img {
  display: block;
  height: auto;
  width: 220px;
  max-width: 100%;
  transition: opacity 0.15s;
}
.site-footer .gwu-mark:hover img,
.site-footer .gwu-mark:focus-visible img { opacity: 0.78; }
.site-footer .gwu-mark:focus-visible {
  outline: 2px solid #1a4a6e; outline-offset: 4px;
}
</style>
"""


def _footer_html() -> str:
    logo_src = _gwu_logo_src()
    if logo_src:
        gwu_block = (
            f'<a class="gwu-mark" href="{_GWU_DEPT_URL}" target="_blank" '
            f'rel="noopener" aria-label="The George Washington University, '
            f'Department of Geography &amp; Environment (opens in new tab)">'
            f'<img src="{logo_src}" '
            f'alt="GW Department of Geography &amp; Environment, '
            f'Columbian College of Arts &amp; Sciences"></a>'
        )
    else:
        # Fallback if the PNG is missing — keep the attribution visible.
        gwu_block = (
            f'<a class="gwu-mark" href="{_GWU_DEPT_URL}" target="_blank" '
            f'rel="noopener" style="color:#1a4a6e;text-decoration:none;">'
            "GW Department of Geography &amp; Environment</a>"
        )

    return f"""
<div class="site-footer">
  <div class="footer-inner">
    <p class="footer-text">
      Created by <a href="https://geography.columbian.gwu.edu/michael-mann" target="_blank" rel="noopener">Michael Mann, PhD</a>.
      Data sources: rainfall &mdash;
      <a href="https://www.chc.ucsb.edu/data/chirps" target="_blank" rel="noopener">CHIRPS</a> (UCSB Climate Hazards Center)
      and <a href="https://gpm.nasa.gov/data/imerg" target="_blank" rel="noopener">IMERG</a> (NASA);
      soil moisture &mdash;
      <a href="https://smap.jpl.nasa.gov/" target="_blank" rel="noopener">SMAP L4</a> (NASA);
      evapotranspiration &mdash;
      <a href="https://wapor.apps.fao.org/" target="_blank" rel="noopener">WAPOR</a> (FAO);
      El Ni&ntilde;o index &mdash;
      <a href="https://origin.cpc.ncep.noaa.gov/products/analysis_monitoring/ensostuff/ONI_v5.php" target="_blank" rel="noopener">ONI</a> (NOAA);
      administrative boundaries &mdash; FAO GAUL.
      This site is independent and not affiliated with or endorsed by any data provider.
      Indicators and forecasts are produced by this dashboard and are provided without
      warranty of accuracy or fitness for any purpose.
    </p>
    {gwu_block}
  </div>
</div>
"""


def render() -> None:
    """Render the site footer at the current Streamlit cursor position.
    Call once near the bottom of `dashboard/app.py`, after all tabs."""
    st.markdown(_FOOTER_CSS + _footer_html(), unsafe_allow_html=True)
