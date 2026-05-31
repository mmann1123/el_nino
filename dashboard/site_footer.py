"""Site-wide footer for the Streamlit dashboard — attribution, data sources,
disclaimer, and GWU Department of Geography & Environment mark.

Matches the landing page's footer copy so both surfaces present the same
attribution. Rendered via a single st.markdown(unsafe_allow_html=True) call
so the inline CSS controls layout (two columns on desktop, stacked on mobile).
"""

from __future__ import annotations

import streamlit as st


_FOOTER_HTML = """
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
    <div class="gwu-mark" aria-label="The George Washington University, Department of Geography &amp; Environment">
      <span class="gwu-monogram" aria-hidden="true">GW</span>
      <span class="gwu-lines">
        <strong>Department of Geography &amp; Environment</strong>
        <span>Columbian College of Arts &amp; Sciences</span>
      </span>
    </div>
  </div>
</div>
"""


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
    align-items: flex-start;
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
.site-footer .gwu-mark {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  flex-shrink: 0;
}
.site-footer .gwu-monogram {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.6rem;
  height: 2.6rem;
  background: #033C5A;
  color: #fff;
  font-weight: 700;
  font-size: 0.95rem;
  letter-spacing: 0.04em;
  border-radius: 3px;
  flex-shrink: 0;
}
.site-footer .gwu-lines { line-height: 1.3; }
.site-footer .gwu-lines strong {
  display: block;
  font-size: 0.78rem;
  font-weight: 600;
  color: #2a2a2a;
}
.site-footer .gwu-lines span {
  display: block;
  font-size: 0.68rem;
  color: #6b6b6b;
}
</style>
"""


def render() -> None:
    """Render the site footer at the current Streamlit cursor position.
    Call once near the bottom of `dashboard/app.py`, after all tabs."""
    st.markdown(_FOOTER_CSS + _FOOTER_HTML, unsafe_allow_html=True)
