from .base import Indicator
from .chirps import CHIRPS
from .smap import SMAP
from .ssebop import SSEBop
from .imerg import IMERG

INDICATORS: dict[str, type[Indicator]] = {
    "chirps": CHIRPS,
    "smap": SMAP,
    "ssebop": SSEBop,
    "imerg": IMERG,
}
