"""U.S. Drought Monitor classification — what non-technical users actually
recognize. SPI / standardized-anomaly thresholds in, plain-language labels
and colors out. Symmetric wet/dry tiers because the dashboard also tracks
overly-wet seasons (which cause their own crop problems: late planting,
fungal disease, lodging).
"""

from __future__ import annotations

from dataclasses import dataclass

from scipy.stats import norm


DARK_INK = "#37474f"   # for use on light backgrounds


@dataclass
class DroughtCategory:
    label: str
    short: str          # USDM-style code (D0..D4, W1..W3, N, ?)
    color: str          # hex
    description: str
    text_color: str = "white"
    is_pending: bool = False


PENDING = DroughtCategory(
    "Computing…", "?", "#cfd8dc",
    "Not enough data yet to classify. The historical baseline or recent observations are still being computed.",
    text_color=DARK_INK,
    is_pending=True,
)
NORMAL = DroughtCategory(
    "Normal", "N", "#a5d6a7",   # Material light green; reads as "OK / healthy"
    "Conditions are within the typical range for this time of year.",
    text_color=DARK_INK,
)
# Wet tiers mirror the dry tiers symmetrically.
W1 = DroughtCategory(
    "Wetter than usual", "W1", "#90caf9",
    "Wetter than typical for this time of year. Watch for delayed planting or fungal pressure.",
    text_color=DARK_INK,
)
W2 = DroughtCategory(
    "Very wet", "W2", "#42a5f5",
    "Substantially wetter than typical. Flood risk in low-lying fields; later-season planting may slip.",
)
W3 = DroughtCategory(
    "Extremely wet", "W3", "#1565c0",
    "Extremely wet conditions for this time of year. Likely waterlogging, lost yield in affected zones.",
)
D0 = DroughtCategory(
    "Abnormally Dry", "D0", "#fff176",
    "Going into drought or recovering from drought. Watch closely.",
    text_color=DARK_INK,
)
D1 = DroughtCategory(
    "Moderate Drought", "D1", "#ffb74d",
    "Some damage to crops; streams and soil moisture below normal.",
    text_color=DARK_INK,
)
D2 = DroughtCategory(
    "Severe Drought", "D2", "#fb8c00",
    "Crop losses likely; water shortages common.",
)
D3 = DroughtCategory(
    "Extreme Drought", "D3", "#e53935",
    "Major crop losses; widespread water shortages.",
)
D4 = DroughtCategory(
    "Exceptional Drought", "D4", "#b71c1c",
    "Exceptional and widespread crop losses; emergency water shortages.",
)


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
        return "Not enough data yet to compare to the typical range."
    pct = norm.cdf(z) * 100
    if z >= 0:
        return f"This value is wetter than {pct:.0f}% of years on record for this time of year."
    return f"This value is in the driest {pct:.0f}% of years on record for this time of year."
