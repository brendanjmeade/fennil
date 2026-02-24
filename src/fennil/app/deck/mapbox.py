import os

import pydeck as pdk
from dotenv import load_dotenv

TOKEN_ENV_KEY = "FENNIL_MAP_BOX_TOKEN"


load_dotenv()
TOKEN = os.getenv(TOKEN_ENV_KEY, "").strip().strip('"').strip("'")
HAS_MAPBOX_TOKEN = bool(TOKEN)

PROVIDER = "mapbox" if HAS_MAPBOX_TOKEN else "carto"
STYLE = "mapbox://styles/mapbox/light-v9" if HAS_MAPBOX_TOKEN else pdk.map_styles.LIGHT

__all__ = [
    "PROVIDER",
    "STYLE",
    "TOKEN",
]
