"""U.S. Drought Monitor classification — what non-technical users actually
recognize. SPI / standardized-anomaly thresholds in, plain-language labels
and colors out.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from scipy.stats import norm


@dataclass
class DroughtCategory:
    label: str
    short: str  # USDM code (D0..D4 or special)
    color: str  # hex
    description: str


WETTER = DroughtCategory("Wetter than usual", "W", "#1f77b4",
                         "Conditions are wetter than typical for this time of year.")
NORMAL = DroughtCategory("Normal", "N", "#9e9e9e",
                         "Conditions are within the typical range for this time of year.")
D0 = DroughtCategory("Abnormally Dry", "D0", "#fff176",
                     "Going into drought or recovering from drought. Watch closely.")
D1 = DroughtCategory("Moderate Drought", "D1", "#ffb74d",
                     "Some damage to crops; streams and soil moisture below normal.")
D2 = DroughtCategory("Severe Drought", "D2", "#fb8c00",
                     "Crop losses likely; water shortages common.")
D3 = DroughtCategory("Extreme Drought", "D3", "#e53935",
                     "Major crop losses; widespread water shortages.")
D4 = DroughtCategory("Exceptional Drought", "D4", "#b71c1c",
                     "Exceptional and widespread crop losses; emergency water shortages.")


def classify(z: float | None) -> DroughtCategory:
    """Map a standardized anomaly (z-score / SPI) to a USDM category.

    Thresholds follow the U.S. Drought Monitor's SPI convention.
    """
    if z is None or (isinstance(z, float) and (z != z)):  # NaN check
        return NORMAL
    if z > 1.0:
        return WETTER
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
