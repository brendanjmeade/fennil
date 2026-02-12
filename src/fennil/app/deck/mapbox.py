import os
from pathlib import Path

import pydeck as pdk


def _load_mapbox_token():
    token = os.getenv("FENNIL_MAP_BOX_TOKEN")
    if token:
        return token
    # Fallback: read from a local .env if present
    for parent in Path(__file__).resolve().parents:
        env_file = parent / ".env"
        if env_file.is_file():
            for line in env_file.read_text().splitlines():
                if line.strip().startswith("FENNIL_MAP_BOX_TOKEN="):
                    return line.split("=", 1)[1].strip()
    return None


mapbox_access_token = _load_mapbox_token()
HAS_MAPBOX_TOKEN = bool(mapbox_access_token)

PROVIDER = "mapbox" if HAS_MAPBOX_TOKEN else "carto"
STYLE = "mapbox://styles/mapbox/light-v9" if HAS_MAPBOX_TOKEN else pdk.map_styles.LIGHT
TOKEN = mapbox_access_token if HAS_MAPBOX_TOKEN else ""

__all__ = [
    "PROVIDER",
    "STYLE",
    "TOKEN",
]
