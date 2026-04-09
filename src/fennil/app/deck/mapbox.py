import json
import os
from pathlib import Path

import pydeck as pdk
from dotenv import load_dotenv

TOKEN_ENV_KEY = "FENNIL_MAP_BOX_TOKEN"
MONOCHROME_STYLE_PATH = Path(__file__).with_name(
    "mapbox_monochrome_bathymetry_style.json"
)


load_dotenv()
TOKEN = os.getenv(TOKEN_ENV_KEY, "").strip().strip('"').strip("'")
HAS_MAPBOX_TOKEN = bool(TOKEN)


def _load_monochrome_mapbox_style():
    # Local monochrome style with a custom bathymetry layer.
    return json.loads(MONOCHROME_STYLE_PATH.read_text(encoding="utf-8"))


PROVIDER = "mapbox" if HAS_MAPBOX_TOKEN else "carto"
STYLE = _load_monochrome_mapbox_style() if HAS_MAPBOX_TOKEN else pdk.map_styles.LIGHT

__all__ = [
    "PROVIDER",
    "STYLE",
    "TOKEN",
]
