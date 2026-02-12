from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .deck.faults import (
    REQUIRED_SEG_COLS,
    fault_projection_layers,
    segment_color_layers,
)
from .deck.stations import station_layers
from .deck.tde import tde_mesh_layers, tde_perimeter_layers
from .deck.vectors import velocity_layers


@dataclass(frozen=True)
class FieldSpec:
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
        self._order: list[str] = []

    def register(self, field_name: str, spec: FieldSpec, builder):
        self._specs[field_name] = spec
        self._builders[field_name] = builder
        if field_name not in self._order:
            self._order.append(field_name)

    def defaults(self):
        return {name: self._specs[name].default for name in self._order}

    def names(self):
        return list(self._order)

    def export_specs(self):
        return {name: spec.to_dict() for name, spec in self._specs.items()}

    def apply(self, name, ctx: LayerContext):
        builder = self._builders.get(name)
        if not builder:
            return
        value = ctx.config.fields.get(name, self._specs[name].default)
        builder(ctx, value)


FIELD_REGISTRY = FieldRegistry()


def _velocity_builder(layer_id, east_attr, north_attr, color_key):
    def builder(ctx: LayerContext, value):
        if not value:
            return
        station = ctx.station
        ctx.vector_layers.extend(
            velocity_layers(
                layer_id,
                station,
                ctx.x_station,
                ctx.y_station,
                getattr(station, east_attr).values,
                getattr(station, north_attr).values,
                ctx.colors[color_key],
                ctx.base_width,
                ctx.folder_number,
                ctx.velocity_scale,
            )
        )

    return builder


def _locs_builder(ctx: LayerContext, value):
    if not value:
        return
    ctx.layers.extend(station_layers(ctx.folder_number, ctx.station, ctx.colors["loc"]))


def _tde_builder(ctx: LayerContext, value):
    if not value:
        return
    data = ctx.config.data
    if not data.tde_available:
        return
    tde_df = data.tde_df
    if tde_df is not None and not tde_df.empty:
        slip_values = (
            tde_df["ss_rate"].to_numpy()
            if value == "ss"
            else tde_df["ds_rate"].to_numpy()
        )
        ctx.tde_layers.extend(tde_mesh_layers(ctx.folder_number, tde_df, slip_values))
    ctx.tde_layers.extend(tde_perimeter_layers(ctx.folder_number, data.tde_perim_df))


def _slip_builder(ctx: LayerContext, value):
    if not value:
        return
    data = ctx.config.data
    if not REQUIRED_SEG_COLS.issubset(data.segment.columns):
        return
    ctx.layers.extend(
        segment_color_layers(
            ctx.folder_number,
            data.segment,
            value,
            ctx.seg_tooltip_enabled,
            ctx.fault_lines_df,
        )
    )


def _fault_proj_builder(ctx: LayerContext, value):
    if not value:
        return
    data = ctx.config.data
    if not data.fault_proj_available:
        return
    ctx.layers.extend(fault_projection_layers(ctx.folder_number, data.fault_proj_df))


FIELD_REGISTRY.register(
    "locs",
    FieldSpec(
        icon="mdi-circle-medium",
        ui_type="VCheckbox",
        color_key="loc",
        options=None,
        default=False,
    ),
    _locs_builder,
)
FIELD_REGISTRY.register(
    "obs",
    FieldSpec(
        icon="mdi-square-rounded",
        ui_type="VCheckbox",
        color_key="obs",
        options=None,
        default=False,
    ),
    _velocity_builder(
        layer_id="obs_vel",
        east_attr="east_vel",
        north_attr="north_vel",
        color_key="obs",
    ),
)
FIELD_REGISTRY.register(
    "mod",
    FieldSpec(
        icon="mdi-square-rounded",
        ui_type="VCheckbox",
        color_key="mod",
        options=None,
        default=False,
    ),
    _velocity_builder(
        layer_id="mod_vel",
        east_attr="model_east_vel",
        north_attr="model_north_vel",
        color_key="mod",
    ),
)
FIELD_REGISTRY.register(
    "res",
    FieldSpec(
        icon="mdi-vector-line",
        ui_type="VCheckbox",
        color_key="res",
        options=None,
        default=False,
    ),
    _velocity_builder(
        layer_id="res_vel",
        east_attr="model_east_vel_residual",
        north_attr="model_north_vel_residual",
        color_key="res",
    ),
)
FIELD_REGISTRY.register(
    "rot",
    FieldSpec(
        icon="mdi-square-rounded",
        ui_type="VCheckbox",
        color_key="rot",
        options=None,
        default=False,
    ),
    _velocity_builder(
        layer_id="rot_vel",
        east_attr="model_east_vel_rotation",
        north_attr="model_north_vel_rotation",
        color_key="rot",
    ),
)
FIELD_REGISTRY.register(
    "seg",
    FieldSpec(
        icon="mdi-gesture",
        ui_type="VCheckbox",
        color_key="seg",
        options=None,
        default=False,
    ),
    _velocity_builder(
        layer_id="seg_vel",
        east_attr="model_east_elastic_segment",
        north_attr="model_north_elastic_segment",
        color_key="seg",
    ),
)
FIELD_REGISTRY.register(
    "tri",
    FieldSpec(
        icon="mdi-square-rounded",
        ui_type="VCheckbox",
        color_key="tde",
        options=None,
        default=False,
    ),
    _velocity_builder(
        layer_id="tde_vel",
        east_attr="model_east_vel_tde",
        north_attr="model_north_vel_tde",
        color_key="tde",
    ),
)
FIELD_REGISTRY.register(
    "str",
    FieldSpec(
        icon="mdi-square-rounded",
        ui_type="VCheckbox",
        color_key="str",
        options=None,
        default=False,
    ),
    _velocity_builder(
        layer_id="str_vel",
        east_attr="model_east_vel_block_strain_rate",
        north_attr="model_north_vel_block_strain_rate",
        color_key="str",
    ),
)
FIELD_REGISTRY.register(
    "mog",
    FieldSpec(
        icon="mdi-square-rounded",
        ui_type="VCheckbox",
        color_key="mog",
        options=None,
        default=False,
    ),
    _velocity_builder(
        layer_id="mog_vel",
        east_attr="model_east_vel_mogi",
        north_attr="model_north_vel_mogi",
        color_key="mog",
    ),
)
FIELD_REGISTRY.register(
    "slip",
    FieldSpec(
        icon="mdi-square-rounded",
        ui_type="VBtnToggle",
        color_key="tde",
        options=[{"text": "SS", "value": "ss"}, {"text": "DS", "value": "ds"}],
        default=None,
    ),
    _slip_builder,
)
FIELD_REGISTRY.register(
    "tde",
    FieldSpec(
        icon="mdi-square-rounded",
        ui_type="VBtnToggle",
        color_key="tde",
        options=[{"text": "SS", "value": "ss"}, {"text": "DS", "value": "ds"}],
        default=None,
    ),
    _tde_builder,
)
FIELD_REGISTRY.register(
    "fault proj",
    FieldSpec(
        icon="mdi-square-rounded",
        ui_type="VCheckbox",
        color_key=None,
        options=None,
        default=False,
        color=[128, 128, 128, 255],
    ),
    _fault_proj_builder,
)
