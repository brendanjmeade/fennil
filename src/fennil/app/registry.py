from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FieldSpec:
    priority: int
    icon: str
    ui_type: str
    color_key: str | None
    options: list[dict[str, str]] | None
    default: bool | str | None
    color: list[int] | None = None

    def to_dict(self):
        return {
            "icon": self.icon,
            "type": self.ui_type,
            "color_key": self.color_key,
            "options": self.options,
            "color": self.color,
        }


@dataclass
class LayerContext:
    config: Any
    ds_index: int
    folder_number: int
    station: Any
    x_station: Any
    y_station: Any
    velocity_scale: float
    colors: dict[str, Any]
    base_width: int
    tde_layers: list
    layers: list
    vector_layers: list
    fault_lines_df: Any
    seg_tooltip_enabled: bool


class FieldRegistry:
    def __init__(self):
        self._specs: dict[str, FieldSpec] = {}
        self._builders: dict[str, Callable[[LayerContext, Any], None]] = {}

    def register(self, field_name: str, spec: FieldSpec, builder):
        self._specs[field_name] = spec
        self._builders[field_name] = builder

    def field_defaults(self):
        return {name: spec.default for name, spec in self._specs.items()}

    def available_fields(self):
        name_priority = [(name, spec.priority) for name, spec in self._specs.items()]
        return [name for name, _ in sorted(name_priority, key=lambda tup: tup[1])]

    def export_specs(self):
        return {name: spec.to_dict() for name, spec in self._specs.items()}

    def build_layers(self, name, ctx: LayerContext):
        builder = self._builders.get(name)
        if not builder:
            return
        value = ctx.config.fields.get(name, self._specs[name].default)
        builder(ctx, value)


FIELD_REGISTRY = FieldRegistry()
