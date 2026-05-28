from .base import Indicator
from .chirps import CHIRPS
from .smap import SMAP
from .wapor import WAPOR
from .imerg import IMERG

INDICATORS: dict[str, type[Indicator]] = {
    "chirps": CHIRPS,
    "smap": SMAP,
    "wapor": WAPOR,
    "imerg": IMERG,
}
