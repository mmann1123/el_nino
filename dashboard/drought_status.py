"""U.S. Drought Monitor classification — what non-technical users actually
recognize. SPI / standardized-anomaly thresholds in, plain-language labels
and colors out. Symmetric wet/dry tiers because the dashboard also tracks
overly-wet seasons (which cause their own crop problems: late planting,
fungal disease, lodging).
"""

from __future__ import annotations

from dataclasses import dataclass

from scipy.stats import norm

from . import i18n


DARK_INK = "#37474f"   # for use on light backgrounds


@dataclass(frozen=True)
class DroughtCategory:
    """One USDM-style tier. ``label`` / ``description`` resolve through
    ``i18n`` at access time so the same category object renders in whichever
    language the session has active."""

    key: str            # i18n key stem: cat_<key>_label / cat_<key>_desc
    short: str          # USDM-style code (D0..D4, W1..W3, N, ?)
    color: str          # hex
    text_color: str = "white"
    is_pending: bool = False

    @property
    def label(self) -> str:
        return i18n.t(f"cat_{self.key}_label")

    @property
    def description(self) -> str:
        return i18n.t(f"cat_{self.key}_desc")


PENDING = DroughtCategory("pending", "?", "#cfd8dc", text_color=DARK_INK, is_pending=True)
NORMAL = DroughtCategory("normal", "N", "#a5d6a7", text_color=DARK_INK)   # Material light green; reads as "OK / healthy"
# Wet tiers mirror the dry tiers symmetrically.
W1 = DroughtCategory("w1", "W1", "#90caf9", text_color=DARK_INK)
W2 = DroughtCategory("w2", "W2", "#42a5f5")
W3 = DroughtCategory("w3", "W3", "#1565c0")
D0 = DroughtCategory("d0", "D0", "#fff176", text_color=DARK_INK)
D1 = DroughtCategory("d1", "D1", "#ffb74d", text_color=DARK_INK)
D2 = DroughtCategory("d2", "D2", "#fb8c00")
D3 = DroughtCategory("d3", "D3", "#e53935")
D4 = DroughtCategory("d4", "D4", "#b71c1c")


def classify(z: float | None) -> DroughtCategory:
    """Map a standardized anomaly (z-score / SPI) to a USDM-style category.

    Returns PENDING when input is None/NaN so the UI can show "Computing…"
    rather than misleading "Normal."
    """
    if z is None or (isinstance(z, float) and (z != z)):
        return PENDING
    if z >= 2.5:
        return W3
    if z >= 2.0:
        return W2
    if z >= 1.0:
        return W1
    if z > -1.0:
        return NORMAL
    if z > -1.3:
        return D0
    if z > -1.6:
        return D1
    if z > -2.0:
        return D2
    if z > -2.5:
        return D3
    return D4


def plain_language(z: float | None) -> str:
    """One-sentence translation of an anomaly z-score for a non-technical user."""
    if z is None or (isinstance(z, float) and (z != z)):
        return i18n.t("plain_none")
    pct = norm.cdf(z) * 100
    if z >= 0:
        return i18n.t("plain_wet", pct=f"{pct:.0f}")
    return i18n.t("plain_dry", pct=f"{pct:.0f}")
