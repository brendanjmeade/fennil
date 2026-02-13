from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from fennil.app.io import Dataset


@dataclass(frozen=True)
class FieldSpec:
    priority: int
    label: str
    icon: str
    ui_type: str
    options: list[dict[str, str]] | None
    default: bool | str | None
    styles: Any | None = None
    multiple: bool = True

    def to_dict(self):
        return {
            "label": self.label,
            "icon": self.icon,
            "type": self.ui_type,
            "styles": self.styles,
            "options": self.options,
            "multiple": self.multiple,
        }


class LayerContext:
    def __init__(self, specs, datasets, velocity_scale):
        self.specs = specs
        self.datasets = datasets
        self.velocity_scale = velocity_scale
        self.tde_layers = []
        self.layers = []
        self.vector_layers = []

    @property
    def field_names(self):
        return self.datasets[0].available_fields

    @property
    def all_layers(self):
        return self.tde_layers + self.layers + self.vector_layers

    def skip(self, name):
        return all(not (ds.enabled and ds.fields.get(name)) for ds in self.datasets)

    def enabled_datasets(self, name):
        return (
            (i, ds)
            for i, ds in enumerate(self.datasets)
            if ds.enabled and ds.fields.get(name) and name in ds.available_fields
        )


class FieldRegistry:
    def __init__(self):
        self._specs: dict[str, FieldSpec] = {}
        self._builders: dict[str, Callable[[str, LayerContext], None]] = {}
        self._can_render: dict[str, Callable[[Dataset], bool]] = {}

    def register(self, field_name: str, spec: FieldSpec, builder, can_render):
        self._specs[field_name] = spec
        self._builders[field_name] = builder
        self._can_render[field_name] = can_render

    def field_defaults(self):
        return {name: spec.default for name, spec in self._specs.items()}

    def available_fields(self, dataset):
        name_priority = [
            (name, spec.priority)
            for name, spec in self._specs.items()
            if self._can_render[name](dataset)
        ]
        return [name for name, _ in sorted(name_priority, key=lambda tup: tup[1])]

    def export_specs(self):
        return {name: spec.to_dict() for name, spec in self._specs.items()}

    def build_layers(self, ctx: LayerContext):
        for name in ctx.field_names:
            builder = self._builders.get(name)
            if builder is None:
                continue
            builder(name, ctx)


FIELD_REGISTRY = FieldRegistry()
