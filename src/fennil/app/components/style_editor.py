import copy
import math

from trame.app import dataclass
from trame.widgets import html
from trame.widgets import vuetify3 as v3

from fennil.app.viz.colormaps import (
    DEFAULT_COLORMAP_NAME,
    DEFAULT_N_COLORS,
    palette_entries,
    palette_gradient_css,
    parse_colormap_range,
    resolve_palette_name,
    sanitize_n_colors,
)
from fennil.app.viz.styles import normalize_dataset_values

DEFAULT_PRESET = DEFAULT_COLORMAP_NAME
DEFAULT_COLOR_RANGE = (0.0, 1.0)
DEFAULT_PICKER_HEXA = "#000000ff"
DEFAULT_COLORMAP_STEP = 1.0
DEFAULT_COLORMAP_PRECISION = 0
COUPLING_COLORMAP_STEP = 0.01
COUPLING_COLORMAP_PRECISION = 2
COLOR_STYLE_GROUPS = (
    ("colors", "Color"),
    ("colors_negative", "Negative"),
    ("colors_positive", "Positive"),
    ("fill", "Fill"),
    ("line", "Line"),
)
DATASET_GRID_STYLE = "`display:grid;grid-template-columns:repeat(${config.show_dual_column ? 2 : 1}, minmax(0, 1fr));`"
DATASET_CARD_STYLE = "border: 1px solid rgba(127,127,127,0.35); border-radius: 8px;"
MINMAX_GRID_STYLE = "display:grid;grid-template-columns:minmax(0, 1fr) minmax(0, 1fr);"
DRAWER_LAYOUT_STYLE = "height:100%;display:flex;flex-direction:column;"
DRAWER_SCROLL_STYLE = "flex:1 1 auto;overflow-y:auto;"
DRAWER_FOOTER_STYLE = (
    "flex:0 0 auto;"
    "border-top:1px solid rgba(127,127,127,0.35);"
    "background:rgb(var(--v-theme-surface));"
)
COLORMAP_ITEM_STYLE = (
    "height:14px;border:1px solid #666;border-radius:4px;overflow:hidden;"
)


class ColorMapControl(dataclass.StateDataModel):
    field_name = dataclass.Sync(str, "")
    label = dataclass.Sync(str, "")
    icon = dataclass.Sync(str, "")
    icon_color = dataclass.Sync(str, "")

    right_label = dataclass.Sync(str, "Right")
    left_label = dataclass.Sync(str, "Left")
    show_dual_column = dataclass.Sync(bool, False)

    has_colors = dataclass.Sync(bool, False)
    has_colors_negative = dataclass.Sync(bool, False)
    has_colors_positive = dataclass.Sync(bool, False)
    has_fill = dataclass.Sync(bool, False)
    has_line = dataclass.Sync(bool, False)
    has_line_width = dataclass.Sync(bool, False)
    has_colormap = dataclass.Sync(bool, False)
    has_segment_scale = dataclass.Sync(bool, False)
    colormap_menu = dataclass.Sync(bool, False)
    colormap_search = dataclass.Sync(str, "")

    colors_0_hexa = dataclass.Sync(str, DEFAULT_PICKER_HEXA)
    colors_1_hexa = dataclass.Sync(str, DEFAULT_PICKER_HEXA)
    colors_negative_0_hexa = dataclass.Sync(str, DEFAULT_PICKER_HEXA)
    colors_negative_1_hexa = dataclass.Sync(str, DEFAULT_PICKER_HEXA)
    colors_positive_0_hexa = dataclass.Sync(str, DEFAULT_PICKER_HEXA)
    colors_positive_1_hexa = dataclass.Sync(str, DEFAULT_PICKER_HEXA)
    fill_0_hexa = dataclass.Sync(str, DEFAULT_PICKER_HEXA)
    fill_1_hexa = dataclass.Sync(str, DEFAULT_PICKER_HEXA)
    line_0_hexa = dataclass.Sync(str, DEFAULT_PICKER_HEXA)
    line_1_hexa = dataclass.Sync(str, DEFAULT_PICKER_HEXA)

    line_width_0_value = dataclass.Sync(float, 1.0)
    line_width_1_value = dataclass.Sync(float, 1.0)
    line_width_0_valid = dataclass.Sync(bool, True)
    line_width_1_valid = dataclass.Sync(bool, True)
    segment_scale_value = dataclass.Sync(float, 1.0)
    segment_scale_valid = dataclass.Sync(bool, True)

    color_value_min = dataclass.Sync(float, 0.0)
    color_value_max = dataclass.Sync(float, 1.0)
    color_value_min_valid = dataclass.Sync(bool, True)
    color_value_max_valid = dataclass.Sync(bool, True)
    colormap_preset = dataclass.Sync(str, DEFAULT_PRESET)
    colormap_n_colors = dataclass.Sync(int, DEFAULT_N_COLORS)
    colormap_invert = dataclass.Sync(bool, False)
    colormap_use_log_scale = dataclass.Sync(bool, False)
    color_value_precision = dataclass.Sync(int, DEFAULT_COLORMAP_PRECISION)
    color_value_step = dataclass.Sync(float, DEFAULT_COLORMAP_STEP)
    color_range_min = dataclass.Sync(float, DEFAULT_COLOR_RANGE[0])
    color_range_max = dataclass.Sync(float, DEFAULT_COLOR_RANGE[1])
    lut_gradient = dataclass.Sync(
        str, "linear-gradient(90deg, rgb(0,0,0), rgb(255,255,255))"
    )


class StyleEditor:
    def __init__(self, app, datasets):
        self._app = app
        self._state = app.state
        self._datasets = datasets
        self._controls: dict[str, ColorMapControl] = {}
        self._field_order: list[str] = []

        self._state.show_style_editor = False
        self._state.style_editor_error = ""

        for key in (
            "style_editor_picker_open",
            "style_editor_picker_hexa",
            "style_editor_picker_control_id",
            "style_editor_picker_field_name",
        ):
            self._state.client_only(key)

        self._state.style_editor_picker_open = False
        self._state.style_editor_picker_hexa = DEFAULT_PICKER_HEXA
        self._state.style_editor_picker_control_id = ""
        self._state.style_editor_picker_field_name = ""
        self._state.style_editor_colormaps = palette_entries(n_colors=96)

        self.refresh()

    def build_ui(self):
        with v3.VNavigationDrawer(
            location="right",
            temporary=True,
            width=560,
            v_model=("show_style_editor", False),
        ):
            with html.Div(style=DRAWER_LAYOUT_STYLE):
                self._build_toolbar()
                with html.Div(style=DRAWER_SCROLL_STYLE):
                    with v3.VContainer(classes="pa-3"):
                        self._build_field_panels()
                self._build_footer()
            self._build_color_picker_dialog()

    def _build_toolbar(self):
        with v3.VToolbar(density="compact", flat=True):
            v3.VToolbarTitle("Style Editor")
            v3.VSpacer()
            v3.VBtn(
                icon="mdi-close",
                variant="text",
                click="show_style_editor = false",
            )

    def _build_field_panels(self):
        if not self._field_order:
            html.Div(
                "No editable styles found.",
                classes="text-medium-emphasis text-caption",
            )
            return

        with v3.VExpansionPanels(multiple=True):
            for field_name in self._field_order:
                control = self._controls[field_name]
                with control.provide_as("config"):
                    with v3.VExpansionPanel(key=field_name):
                        self._build_panel_title()
                        with v3.VExpansionPanelText():
                            self._build_panel_body(control)

    def _build_panel_title(self):
        with v3.VExpansionPanelTitle():
            with html.Div(classes="d-flex align-center ga-2"):
                v3.VIcon(
                    icon=("config.icon",),
                    color=("config.icon_color || undefined",),
                    size="small",
                )
                html.Div(
                    "{{ config.label }}",
                    classes="text-subtitle-2",
                )

    def _build_panel_body(self, control):
        for key, label in COLOR_STYLE_GROUPS:
            if not getattr(control, f"has_{key}"):
                continue
            self._build_color_group(key, label)

        if control.has_segment_scale:
            self._build_segment_scale_group()

        if control.has_line_width:
            self._build_line_width_group()

        if control.has_colormap:
            self._build_colormap_group()

        if not self._has_editable_groups(control):
            html.Div(
                "No editable styles.",
                classes="text-caption text-medium-emphasis",
            )

    def _build_color_group(self, key, label):
        html.Div(label, classes="text-caption mb-1")
        with html.Div(
            classes="ga-3 mb-2",
            style=[DATASET_GRID_STYLE],
        ):
            self._build_color_card(
                hexa_attr=f"{key}_1_hexa",
                label="{{ config.left_label }}",
                v_show="config.show_dual_column",
            )
            self._build_color_card(
                hexa_attr=f"{key}_0_hexa",
                label="{{ config.right_label }}",
            )

    def _build_line_width_group(self):
        html.Div("Line width", classes="text-caption mb-1")
        with html.Div(
            classes="ga-3 mb-2",
            style=[DATASET_GRID_STYLE],
        ):
            self._build_width_card(
                value_attr="line_width_1_value",
                valid_attr="line_width_1_valid",
                label="{{ config.left_label }}",
                v_show="config.show_dual_column",
            )
            self._build_width_card(
                value_attr="line_width_0_value",
                valid_attr="line_width_0_valid",
                label="{{ config.right_label }}",
            )

    def _build_segment_scale_group(self):
        html.Div("Segment scale", classes="text-caption mb-1")
        with html.Div(classes="mb-2"):
            v3.VNumberInput(
                v_model="config.segment_scale_value",
                label="Width multiplier",
                density="compact",
                hide_details=True,
                variant="outlined",
                control_variant="split",
                classes="mt-2",
                min=[0],
                step=[0.1],
                precision=[2],
                error=("!config.segment_scale_valid",),
                style="max-width: 220px;",
            )

    def _build_colormap_group(self):
        html.Div("Color map range", classes="text-caption mb-1")
        with html.Div(classes="mb-2"):
            self._create_bottom_bar()
        with html.Div(
            classes="ga-3 mb-2",
            style=MINMAX_GRID_STYLE,
        ):
            self._build_colormap_bound_input(
                value_attr="color_value_min",
                valid_attr="color_value_min_valid",
                label="Min",
            )
            self._build_colormap_bound_input(
                value_attr="color_value_max",
                valid_attr="color_value_max_valid",
                label="Max",
            )

    def _build_colormap_bound_input(self, value_attr, valid_attr, label):
        v3.VNumberInput(
            v_model=f"config.{value_attr}",
            hide_details=True,
            density="compact",
            variant="outlined",
            control_variant="split",
            precision=(
                "config.color_value_precision",
                DEFAULT_COLORMAP_PRECISION,
            ),
            step=(
                "config.color_value_step",
                DEFAULT_COLORMAP_STEP,
            ),
            label=label,
            error=(f"!config.{valid_attr}",),
        )

    def _build_footer(self):
        with html.Div(style=DRAWER_FOOTER_STYLE):
            with v3.VContainer(classes="pa-3 pt-2"):
                html.Div(
                    "{{ style_editor_error }}",
                    v_if="style_editor_error",
                    classes="text-error text-caption mb-2",
                )
                if self._field_order:
                    with html.Div(classes="d-flex justify-end"):
                        v3.VBtn(
                            "Apply Styles",
                            color="primary",
                            click=self.apply_all,
                            size="large",
                        )

    def _build_color_picker_dialog(self):
        with v3.VDialog(
            v_model=("style_editor_picker_open", False),
            max_width=360,
        ):
            with v3.VCard():
                with v3.VCardText(classes="pa-2"):
                    v3.VColorPicker(
                        model_value=(
                            "style_editor_picker_hexa",
                            DEFAULT_PICKER_HEXA,
                        ),
                        update_modelValue=(
                            self.update_picker_color,
                            "[style_editor_picker_control_id, style_editor_picker_field_name, $event]",
                        ),
                        mode="hexa",
                        hide_inputs=False,
                        show_swatches=True,
                        elevation=0,
                        width=320,
                        canvas_height=180,
                    )
                with v3.VCardActions(classes="pa-2 pt-0"):
                    v3.VSpacer()
                    v3.VBtn(
                        "Done",
                        variant="text",
                        click="style_editor_picker_open = false",
                    )

    def open(self):
        if self._state.show_style_editor:
            self._state.show_style_editor = False
            return
        self.refresh()
        self._state.show_style_editor = True

    def refresh(self):
        specs = self._state.field_specs or {}
        field_order = []
        active_fields = set()

        for field_name in sorted(
            specs.keys(),
            key=lambda name: specs.get(name, {}).get("priority", 999),
        ):
            spec = specs.get(field_name, {})
            styles = spec.get("styles") or {}

            control = self._controls.get(field_name)
            if control is None:
                control = self._create_control(field_name, spec, styles)
                self._controls[field_name] = control

            self._load_control(control, field_name, spec, styles)
            field_order.append(field_name)
            active_fields.add(field_name)

        for field_name in tuple(self._controls.keys()):
            if field_name in active_fields:
                continue
            del self._controls[field_name]

        self._field_order = field_order
        self._state.style_editor_error = ""

    def apply_all(self, *_):
        updated_specs = copy.deepcopy(self._state.field_specs or {})

        for field_name in self._field_order:
            control = self._controls.get(field_name)
            spec = updated_specs.get(field_name)
            if control is None or spec is None:
                continue

            styles = copy.deepcopy(spec.get("styles") or {})

            for key, _ in COLOR_STYLE_GROUPS:
                if not getattr(control, f"has_{key}"):
                    continue
                try:
                    value_0 = self._parse_color(getattr(control, f"{key}_0_hexa"))
                except ValueError as exc:
                    self._state.style_editor_error = f"{field_name}.{key}[0] {exc}"
                    return
                try:
                    value_1 = self._parse_color(getattr(control, f"{key}_1_hexa"))
                except ValueError as exc:
                    self._state.style_editor_error = f"{field_name}.{key}[1] {exc}"
                    return
                styles[key] = [value_0, value_1]

            if control.has_segment_scale:
                if not control.segment_scale_valid:
                    self._state.style_editor_error = (
                        f"{field_name}.segment_scale must be numeric."
                    )
                    return
                if float(control.segment_scale_value) < 0:
                    self._state.style_editor_error = (
                        f"{field_name}.segment_scale must be >= 0."
                    )
                    return
                styles["segment_scale"] = float(control.segment_scale_value)

            if control.has_line_width:
                if not control.line_width_0_valid:
                    self._state.style_editor_error = (
                        f"{field_name}.line_width[0] must be numeric."
                    )
                    return
                if not control.line_width_1_valid:
                    self._state.style_editor_error = (
                        f"{field_name}.line_width[1] must be numeric."
                    )
                    return
                styles["line_width"] = [
                    float(control.line_width_0_value),
                    float(control.line_width_1_value),
                ]

            if control.has_colormap:
                color_map_range = copy.deepcopy(styles.get("color_map_range") or {})
                if (
                    not control.color_value_min_valid
                    or not control.color_value_max_valid
                ):
                    self._state.style_editor_error = (
                        f"{field_name}.color_map_range min/max must be numeric."
                    )
                    return

                value_min = control.color_range_min
                value_max = control.color_range_max
                if value_min >= value_max:
                    self._state.style_editor_error = (
                        f"{field_name}.color_map_range min must be less than max."
                    )
                    return

                color_map_range["min"] = float(value_min)
                color_map_range["max"] = float(value_max)
                color_map_range["palette"] = resolve_palette_name(
                    control.colormap_preset
                )
                color_map_range["n_colors"] = sanitize_n_colors(
                    control.colormap_n_colors,
                    default=DEFAULT_N_COLORS,
                )
                styles["color_map_range"] = color_map_range

            spec["styles"] = styles

        with self._state:
            self._state.field_specs = updated_specs
            self._state.style_editor_error = ""

    def update_picker_color(self, control_id, field_name, value=None):
        hexa_value = str(
            value if value is not None else self._state.style_editor_picker_hexa
        )
        self._state.style_editor_picker_hexa = hexa_value

        control = dataclass.get_instance(control_id)
        if control is None or not field_name:
            return
        if not hasattr(control, field_name):
            return
        setattr(control, field_name, hexa_value)

    def _create_control(self, field_name, spec, styles):
        control = ColorMapControl(
            self._app.server,
            field_name=field_name,
            label=spec.get("label", field_name),
            icon=spec.get("icon", "mdi-palette"),
            icon_color=str(styles.get("icon_color") or ""),
        )
        control.watch(
            ["color_value_min", "color_value_max"],
            lambda value_min, value_max, name=field_name: (
                self._color_range_str_to_float(
                    name,
                    value_min,
                    value_max,
                )
            ),
            sync=True,
        )
        control.watch(
            ["line_width_0_value", "line_width_1_value"],
            lambda width_0, width_1, name=field_name: self._line_width_str_to_float(
                name,
                width_0,
                width_1,
            ),
            sync=True,
            eager=True,
        )
        control.watch(
            ["segment_scale_value"],
            lambda segment_scale, name=field_name: self._segment_scale_str_to_float(
                name,
                segment_scale,
            ),
            sync=True,
            eager=True,
        )
        control.watch(
            ["colormap_preset", "colormap_n_colors"],
            lambda preset, n_colors, name=field_name: self._sync_colormap_preview(
                name,
                preset,
                n_colors,
            ),
            sync=True,
            eager=True,
        )
        return control

    def _load_control(self, control, field_name, spec, styles):
        control.label = spec.get("label", field_name)
        control.icon = spec.get("icon", "mdi-palette")
        control.icon_color = str(styles.get("icon_color") or "")

        right_label, left_label, show_left_column = self._dataset_labels()
        pair_labels = styles.get("pair_labels")
        if isinstance(pair_labels, list | tuple) and len(pair_labels) >= 2:
            right_label = str(pair_labels[0] or right_label)
            left_label = str(pair_labels[1] or left_label)
            control.show_dual_column = True
        else:
            control.show_dual_column = show_left_column
        control.right_label = right_label
        control.left_label = left_label
        control.show_dual_column = bool(control.show_dual_column)

        for key, _ in COLOR_STYLE_GROUPS:
            self._load_color_group(control, key, styles)

        self._load_segment_scale_group(control, styles)
        self._load_line_width_group(control, styles)
        self._load_colormap_group(control, field_name, styles)

    def _load_color_group(self, control, key, styles):
        value = styles.get(key)
        has_group = isinstance(value, list | tuple)
        setattr(control, f"has_{key}", has_group)
        if not has_group:
            return

        pair = normalize_dataset_values(value, value)
        setattr(control, f"{key}_0_hexa", self._rgba_to_hexa(pair[0]))
        setattr(control, f"{key}_1_hexa", self._rgba_to_hexa(pair[1]))

    def _load_line_width_group(self, control, styles):
        value = styles.get("line_width")
        has_group = isinstance(value, list | tuple)
        control.has_line_width = has_group
        if not has_group:
            return

        pair = normalize_dataset_values(value, value)
        value_0 = self._to_float(pair[0], 1.0)
        value_1 = self._to_float(pair[1], 1.0)
        control.line_width_0_value = value_0
        control.line_width_1_value = value_1
        control.line_width_0_valid = True
        control.line_width_1_valid = True

    def _load_segment_scale_group(self, control, styles):
        has_group = "segment_scale" in styles
        control.has_segment_scale = has_group
        if not has_group:
            return
        control.segment_scale_value = self._to_float(styles.get("segment_scale"), 1.0)
        control.segment_scale_valid = True

    def _load_colormap_group(self, control, field_name, styles):
        color_map_range = styles.get("color_map_range")
        (
            control.color_value_step,
            control.color_value_precision,
        ) = self._colormap_input_settings(field_name)
        control.has_colormap = isinstance(color_map_range, dict)
        if not control.has_colormap:
            return

        colormap = parse_colormap_range(
            color_map_range,
            default_min=DEFAULT_COLOR_RANGE[0],
            default_max=DEFAULT_COLOR_RANGE[1],
            default_palette=DEFAULT_PRESET,
            default_n_colors=DEFAULT_N_COLORS,
        )

        control.color_range_min = colormap["min"]
        control.color_range_max = colormap["max"]
        control.color_value_min = colormap["min"]
        control.color_value_max = colormap["max"]
        control.color_value_min_valid = True
        control.color_value_max_valid = True
        control.colormap_invert = colormap["invert"]
        control.colormap_use_log_scale = colormap["use_log_scale"]
        self._set_colormap_preview(
            control,
            colormap["palette"],
            colormap["n_colors"],
        )

    def _dataset_labels(self):
        right = self._datasets[0] if self._datasets else None
        left = self._datasets[1] if len(self._datasets) > 1 else None
        right_label = (
            right.name
            if right is not None and right.enabled and right.name
            else "Right"
        )
        left_label = (
            left.name if left is not None and left.enabled and left.name else "Left"
        )
        show_left_column = bool(left is not None and left.enabled)
        return right_label, left_label, show_left_column

    @staticmethod
    def _colormap_input_settings(field_name):
        if field_name == "coupling":
            return COUPLING_COLORMAP_STEP, COUPLING_COLORMAP_PRECISION
        return DEFAULT_COLORMAP_STEP, DEFAULT_COLORMAP_PRECISION

    def _sync_colormap_preview(self, field_name, preset, n_colors):
        control = self._controls.get(field_name)
        if control is None:
            return
        if not control.has_colormap:
            return
        self._set_colormap_preview(control, preset, n_colors)

    def _set_colormap_preview(self, control, preset, n_colors):
        palette_name = resolve_palette_name(preset)
        color_count = sanitize_n_colors(n_colors, default=DEFAULT_N_COLORS)
        if control.colormap_preset != palette_name:
            control.colormap_preset = palette_name
        if control.colormap_n_colors != color_count:
            control.colormap_n_colors = color_count
        control.lut_gradient = palette_gradient_css(
            palette_name,
            n_colors=color_count,
            invert=control.colormap_invert,
            use_log_scale=control.colormap_use_log_scale,
        )

    def _line_width_str_to_float(self, field_name, width_0, width_1):
        control = self._controls.get(field_name)
        if control is None:
            return

        parsed_0 = self._parse_finite_float(width_0)
        parsed_1 = self._parse_finite_float(width_1)

        control.line_width_0_valid = parsed_0 is not None
        control.line_width_1_valid = parsed_1 is not None
        if parsed_0 is not None:
            control.line_width_0_value = parsed_0
        if parsed_1 is not None:
            control.line_width_1_value = parsed_1

    def _segment_scale_str_to_float(self, field_name, segment_scale):
        control = self._controls.get(field_name)
        if control is None:
            return
        parsed = self._parse_finite_float(segment_scale)
        control.segment_scale_valid = parsed is not None
        if parsed is not None:
            control.segment_scale_value = parsed

    def _color_range_str_to_float(self, field_name, color_value_min, color_value_max):
        control = self._controls.get(field_name)
        if control is None:
            return

        value_min = self._parse_finite_float(color_value_min)
        value_max = self._parse_finite_float(color_value_max)
        control.color_value_min_valid = value_min is not None
        control.color_value_max_valid = value_max is not None
        if value_min is not None and value_max is not None:
            control.color_range_min = value_min
            control.color_range_max = value_max

    def _build_color_card(self, hexa_attr, label, v_show=None):
        with html.Div(
            classes="pa-2",
            style=DATASET_CARD_STYLE,
            v_show=v_show,
        ):
            html.Div(label, classes="text-caption mb-2")
            with html.Div(classes="d-flex align-center ga-2"):
                v3.VBtn(
                    "",
                    variant="flat",
                    density="compact",
                    size="small",
                    style=[self._swatch_style(hexa_attr)],
                    click=self._open_picker_js(hexa_attr),
                )
                v3.VTextField(
                    v_model=f"config.{hexa_attr}",
                    label="HEXA",
                    density="compact",
                    hide_details=True,
                    variant="outlined",
                    style="min-width: 0; flex: 1 1 auto;",
                )

    def _build_width_card(self, value_attr, valid_attr, label, v_show=None):
        with html.Div(
            classes="pa-2",
            style=DATASET_CARD_STYLE,
            v_show=v_show,
        ):
            html.Div(label, classes="text-caption mb-2")
            v3.VNumberInput(
                v_model=f"config.{value_attr}",
                label="Line Width",
                density="compact",
                hide_details=True,
                variant="outlined",
                control_variant="split",
                error=(f"!config.{valid_attr}",),
                style="min-width: 0;",
            )

    @staticmethod
    def _has_editable_groups(control):
        return bool(
            control.has_colors
            or control.has_fill
            or control.has_line
            or control.has_segment_scale
            or control.has_line_width
            or control.has_colormap
        )

    @staticmethod
    def _swatch_style(hexa_attr):
        return (
            f"`width:32px;height:32px;min-width:32px;border-radius:50%;"
            f"border:1px solid #666;background:${{config.{hexa_attr}}};`"
        )

    @staticmethod
    def _open_picker_js(hexa_attr):
        return (
            "style_editor_picker_open = true;"
            "style_editor_picker_control_id = config._id;"
            f"style_editor_picker_field_name = '{hexa_attr}';"
            f"style_editor_picker_hexa = config.{hexa_attr};"
        )

    def _create_bottom_bar(self):
        with html.Div(
            classes="text-black d-flex align-center",
            style="user-select:none;cursor:context-menu;",
        ):
            with v3.VMenu(
                v_model="config.colormap_menu",
                activator="parent",
                location="top",
                close_on_content_click=False,
            ):
                with v3.VCard(style="max-width: 360px;min-width: 360px;"):
                    with v3.VCardItem(classes="py-1 px-2"):
                        v3.VTextField(
                            v_model="config.colormap_search",
                            clearable=True,
                            click_clear="config.colormap_search = null",
                            placeholder=("config.colormap_preset",),
                            single_line=True,
                            variant="solo",
                            density="compact",
                            hide_details="auto",
                            flat=True,
                        )
                    with v3.VCardItem(classes="py-1 mb-2"):
                        v3.VNumberInput(
                            v_model="config.colormap_n_colors",
                            hide_details=True,
                            density="compact",
                            variant="outlined",
                            flat=True,
                            label="Number of colors",
                            classes="mt-2",
                            step=[1],
                            min=[2],
                            max=[255],
                        )
                    v3.VDivider()
                    with v3.VList(density="compact", max_height="40vh"):
                        with v3.VListItem(
                            v_for="entry in style_editor_colormaps",
                            key="entry.name",
                            v_show=(
                                "config.colormap_search?.length ? entry.name.toLowerCase().includes(config.colormap_search.toLowerCase()) : true",
                            ),
                            active=("config.colormap_preset === entry.name",),
                            click="config.colormap_preset = entry.name; config.colormap_menu = false",
                        ):
                            html.Div(
                                "{{ entry.name }}",
                                classes="text-caption mb-1",
                            )
                            html.Div(
                                style=[
                                    f"`width:100%;{COLORMAP_ITEM_STYLE}background:${{entry.gradient}};`"
                                ],
                            )

            html.Div(
                "{{ config.color_value_min }}",
                classes="text-caption px-2 text-no-wrap",
            )
            with html.Div(
                classes="w-100",
                style=COLORMAP_ITEM_STYLE,
            ):
                html.Div(
                    style=[
                        "`width:100%;height:100%;background:${config.lut_gradient};`"
                    ],
                )
            html.Div(
                "{{ config.color_value_max }}",
                classes="text-caption px-2 text-no-wrap",
            )

    @staticmethod
    def _to_float(value, fallback):
        try:
            value = float(value)
            if math.isfinite(value):
                return value
        except (TypeError, ValueError):
            pass
        return float(fallback)

    @staticmethod
    def _parse_finite_float(value):
        try:
            parsed = float(value)
            if math.isfinite(parsed):
                return parsed
        except (TypeError, ValueError):
            pass
        return None

    @staticmethod
    def _rgba_to_hexa(value):
        rgba = list(value) if isinstance(value, list | tuple) else [0, 0, 0, 255]
        while len(rgba) < 4:
            rgba.append(255)
        r, g, b, a = (max(0, min(255, int(float(c)))) for c in rgba[:4])
        return f"#{r:02x}{g:02x}{b:02x}{a:02x}"

    @staticmethod
    def _parse_color(hexa_value):
        value = str(hexa_value or "").strip()
        if value.startswith("#"):
            value = value[1:]
        if len(value) == 6:
            value += "ff"
        if len(value) != 8:
            msg = "color must be #RRGGBBAA (or #RRGGBB)."
            raise ValueError(msg)
        try:
            r = int(value[0:2], 16)
            g = int(value[2:4], 16)
            b = int(value[4:6], 16)
            a = int(value[6:8], 16)
        except ValueError as exc:
            msg = "invalid color channel."
            raise ValueError(msg) from exc
        return [r, g, b, a]
