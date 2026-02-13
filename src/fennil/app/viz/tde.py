from fennil.app.deck.tde import tde_mesh_layers, tde_perimeter_layers
from fennil.app.registry import FieldSpec, LayerContext

SPEC = FieldSpec(
    priority=21,
    icon="mdi-texture-box",
    ui_type="VBtnToggle",
    color_key="tde",
    options=[
        {"text": "SS", "value": "ss"},
        {"text": "DS", "value": "ds"},
    ],
    default=None,
)


def builder(ctx: LayerContext, value):
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
