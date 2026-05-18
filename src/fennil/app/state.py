from pathlib import Path

from trame.app import dataclass

from fennil.app.io import Dataset
from fennil.app.registry import FIELD_REGISTRY

DEFAULT_VIEW_STATE = {
    "latitude": 35.0,
    "longitude": -165.0,
    "zoom": 2,
    "pitch": 0,
    "bearing": 0,
}


class MapSettings(dataclass.StateDataModel):
    latitude = dataclass.Sync(float, DEFAULT_VIEW_STATE["latitude"])
    longitude = dataclass.Sync(float, DEFAULT_VIEW_STATE["longitude"])
    zoom = dataclass.Sync(float, DEFAULT_VIEW_STATE["zoom"])
    pitch = dataclass.Sync(float, DEFAULT_VIEW_STATE["pitch"])
    bearing = dataclass.Sync(float, DEFAULT_VIEW_STATE["bearing"])


class DatasetVisualization(dataclass.StateDataModel):
    enabled = dataclass.Sync(bool, False)
    name = dataclass.Sync(str, "")
    fields = dataclass.Sync(dict[str, bool | str | None], dict)
    available_fields = dataclass.Sync(list[str], list)
    data = dataclass.ServerOnly(Dataset)

    def attach_data(self, directory_path, data):
        self.data = data
        self.name = ""
        self.enabled = bool(data)
        if data:
            self.name = Path(directory_path).stem.lstrip("0")
            self.available_fields = FIELD_REGISTRY.available_fields(data)
            self.fields = FIELD_REGISTRY.field_defaults()

    def clear(self):
        self.enabled = False
        self.fields = {}
        self.available_fields = []

    def adopt(self, other):
        self.data = other.data
        self.name = other.name
        self.enabled = other.enabled
        self.fields = dict(other.fields)
        self.available_fields = list(other.available_fields)
