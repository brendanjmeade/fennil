from pathlib import Path

from trame_dataclass.core import StateDataModel

from fennil.app.registry import FIELD_REGISTRY

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

    def attach_data(self, directory_path, data):
        self._data = data
        self.name = ""
        self.enabled = bool(data)
        if data:
            self.name = Path(directory_path).stem.lstrip("0")
            self.available_fields = FIELD_REGISTRY.available_fields(data)
            self.fields = FIELD_REGISTRY.field_defaults()

    @property
    def data(self):
        return getattr(self, "_data", None)

    def clear(self):
        self.enabled = False
        self.fields = {}
        self.available_fields = []
