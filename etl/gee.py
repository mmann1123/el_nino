"""Earth Engine init. Service account in cloud; interactive locally."""

from __future__ import annotations

import json

import ee

from .. import config

_initialized = False


def init() -> None:
    global _initialized
    if _initialized:
        return

    if config.GEE_SERVICE_ACCOUNT_JSON:
        info = json.loads(config.GEE_SERVICE_ACCOUNT_JSON)
        credentials = ee.ServiceAccountCredentials(info["client_email"], key_data=config.GEE_SERVICE_ACCOUNT_JSON)
        ee.Initialize(credentials, project=config.GEE_PROJECT or None)
    else:
        if config.GEE_PROJECT:
            ee.Initialize(project=config.GEE_PROJECT)
        else:
            ee.Initialize()
    _initialized = True
