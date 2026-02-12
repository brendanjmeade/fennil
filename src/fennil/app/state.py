from pathlib import Path
from typing import ClassVar

from trame_dataclass.core import StateDataModel

DEFAULT_VIEW_STATE = {
    "latitude": 35.0,
    "longitude": -165.0,
    "zoom": 2,
    "pitch": 0,
    "bearing": 0,
}


class MapSettings(StateDataModel):
    latitude: float = DEFAULT_VIEW_STATE["latitude"]
    longitude: float = DEFAULT_VIEW_STATE["longitude"]
    zoom: float = DEFAULT_VIEW_STATE["zoom"]
    pitch: float = DEFAULT_VIEW_STATE["pitch"]
    bearing: float = DEFAULT_VIEW_STATE["bearing"]


class DatasetVisualization(StateDataModel):
    enabled: bool = False
    name: str
    fields: dict[str, bool | str | None]
    available_fields: list[str]
    colors: dict[str, list[int]] | None

    def attach_data(self, directory_path, data, colors):
        from .fields import FIELD_REGISTRY

        self._data = data

        self.name = ""
        self.enabled = bool(data)
        if data:
            self.name = Path(directory_path).stem.lstrip("0")
            self.available_fields = FIELD_REGISTRY.names()
            self.fields = FIELD_REGISTRY.defaults()
            self.colors = colors

    @property
    def data(self):
        return getattr(self, "_data", None)

    def clear(self):
        self.enabled = False
        self.fields = {}
        self.available_fields = []
        self.colors = None


class AppState(StateDataModel):
    velocity_scale: float = 1.0
    velocity_scale_display: str = "1"
    folder_1_path: str = "---"
    folder_2_path: str = "---"
    folder_1_full_path: str = ""
    folder_2_full_path: str = ""
    show_res_compare: bool = False
    map_latitude: float = DEFAULT_VIEW_STATE["latitude"]
    map_longitude: float = DEFAULT_VIEW_STATE["longitude"]
    map_zoom: float = DEFAULT_VIEW_STATE["zoom"]
    map_pitch: float = DEFAULT_VIEW_STATE["pitch"]
    map_bearing: float = DEFAULT_VIEW_STATE["bearing"]


class FolderState:
    DEFAULTS: ClassVar[dict[str, object]] = {
        "show_locs": False,
        "show_obs": False,
        "show_mod": False,
        "show_res": False,
        "show_rot": False,
        "show_seg": False,
        "show_tri": False,
        "show_str": False,
        "show_mog": False,
        "show_res_mag": False,
        "show_seg_color": False,
        "seg_slip_type": "ss",
        "show_tde": False,
        "tde_slip_type": "ss",
        "show_fault_proj": False,
    }

    def __init__(self, state, prefix):
        self._state = state
        self._prefix = prefix
        for key, value in self.DEFAULTS.items():
            self._state.setdefault(self.key(key), value)

    def key(self, name):
        return f"{self._prefix}_{name}"

    def get(self, name, default=None):
        return self._state.get(self.key(name), default)

    def __getitem__(self, name):
        return self._state[self.key(name)]

    def __setitem__(self, name, value):
        self._state[self.key(name)] = value
