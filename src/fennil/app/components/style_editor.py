import copy
import math

from trame.widgets import html
from trame.widgets import vuetify3 as v3
from trame_dataclass.core import StateDataModel, get_instance

from fennil.app.viz.styles import RDBU_11, normalize_dataset_values

DEFAULT_PRESET = "RDBU_11"
DEFAULT_COLOR_RANGE = (0.0, 1.0)
DEFAULT_N_COLORS = 11
DEFAULT_PICKER_HEXA = "#000000ff"
DEFAULT_COLORMAP_STEP = 1.0
DEFAULT_COLORMAP_PRECISION = 0
COUPLING_COLORMAP_STEP = 0.01
COUPLING_COLORMAP_PRECISION = 2
PALETTES = {
    "RDBU_11": RDBU_11,
}
COLOR_STYLE_GROUPS = (
    ("colors", "Color"),
    ("fill", "Fill"),
    ("line", "Line"),
)
DATASET_GRID_STYLE = "`display:grid;grid-template-columns:repeat(${config.show_left_column ? 2 : 1}, minmax(0, 1fr));`"
DATASET_CARD_STYLE = "border: 1px solid rgba(127,127,127,0.35); border-radius: 8px;"
MINMAX_GRID_STYLE = "display:grid;grid-template-columns:minmax(0, 1fr) minmax(0, 1fr);"
DRAWER_LAYOUT_STYLE = "height:100%;display:flex;flex-direction:column;"
DRAWER_SCROLL_STYLE = "flex:1 1 auto;overflow-y:auto;"
DRAWER_FOOTER_STYLE = (
    "flex:0 0 auto;"
    "border-top:1px solid rgba(127,127,127,0.35);"
    "background:rgb(var(--v-theme-surface));"
)


class ColorMapControl(StateDataModel):
    field_name: str
    label: str
    icon: str
    icon_color: str

    right_label: str = "Right"
    left_label: str = "Left"
    show_left_column: bool = False

    has_colors: bool = False
    has_fill: bool = False
    has_line: bool = False
    has_line_width: bool = False
    has_colormap: bool = False

    colors_0_hexa: str = DEFAULT_PICKER_HEXA
    colors_1_hexa: str = DEFAULT_PICKER_HEXA
    fill_0_hexa: str = DEFAULT_PICKER_HEXA
    fill_1_hexa: str = DEFAULT_PICKER_HEXA
    line_0_hexa: str = DEFAULT_PICKER_HEXA
    line_1_hexa: str = DEFAULT_PICKER_HEXA

    line_width_0_value: float = 1.0
    line_width_1_value: float = 1.0
    line_width_0_valid: bool = True
    line_width_1_valid: bool = True

    color_value_min: float = 0.0
    color_value_max: float = 1.0
    color_value_min_valid: bool = True
    color_value_max_valid: bool = True
    color_value_precision: int = DEFAULT_COLORMAP_PRECISION
    color_value_step: float = DEFAULT_COLORMAP_STEP
    color_range_min: float = DEFAULT_COLOR_RANGE[0]
    color_range_max: float = DEFAULT_COLOR_RANGE[1]
    lut_gradient: str = "linear-gradient(90deg, rgb(0,0,0), rgb(255,255,255))"


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
                v_show="config.show_left_column",
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
                v_show="config.show_left_column",
            )
            self._build_width_card(
                value_attr="line_width_0_value",
                valid_attr="line_width_0_valid",
                label="{{ config.right_label }}",
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

        control = get_instance(control_id)
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
            lambda value_min,
            value_max,
            name=field_name: self._color_range_str_to_float(
                name,
                value_min,
                value_max,
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
        return control

    def _load_control(self, control, field_name, spec, styles):
        control.label = spec.get("label", field_name)
        control.icon = spec.get("icon", "mdi-palette")
        control.icon_color = str(styles.get("icon_color") or "")

        right_label, left_label, show_left_column = self._dataset_labels()
        control.right_label = right_label
        control.left_label = left_label
        control.show_left_column = show_left_column

        for key, _ in COLOR_STYLE_GROUPS:
            self._load_color_group(control, key, styles)

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

    def _load_colormap_group(self, control, field_name, styles):
        color_map_range = styles.get("color_map_range")
        (
            control.color_value_step,
            control.color_value_precision,
        ) = self._colormap_input_settings(field_name)
        control.has_colormap = isinstance(color_map_range, dict)
        if not control.has_colormap:
            return

        value_min = self._to_float(
            color_map_range.get("min", DEFAULT_COLOR_RANGE[0]),
            DEFAULT_COLOR_RANGE[0],
        )
        value_max = self._to_float(
            color_map_range.get("max", DEFAULT_COLOR_RANGE[1]),
            DEFAULT_COLOR_RANGE[1],
        )
        preset = self._palette_name(color_map_range.get("palette", DEFAULT_PRESET))
        invert = bool(color_map_range.get("invert", False))
        use_log_scale = bool(color_map_range.get("use_log_scale", False))
        n_colors = self._sanitize_n_colors(
            color_map_range.get("n_colors", DEFAULT_N_COLORS)
        )

        control.color_range_min = value_min
        control.color_range_max = value_max
        control.color_value_min = value_min
        control.color_value_max = value_max
        control.color_value_min_valid = True
        control.color_value_max_valid = True
        control.lut_gradient = self._palette_gradient(
            preset,
            invert,
            n_colors,
            use_log_scale,
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
            style="user-select:none;",
        ):
            html.Div(
                "{{ config.color_value_min }}",
                classes="text-caption px-2 text-no-wrap",
            )
            with html.Div(
                classes="w-100",
                style="height:14px;border:1px solid #666;border-radius:4px;overflow:hidden;",
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

    @staticmethod
    def _sanitize_n_colors(value):
        try:
            value = int(value)
        except (TypeError, ValueError):
            return DEFAULT_N_COLORS
        return max(2, min(255, value))

    @staticmethod
    def _palette_name(value):
        palette_name = str(value)
        if palette_name in PALETTES:
            return palette_name
        return DEFAULT_PRESET

    @staticmethod
    def _palette_data(name):
        palette = PALETTES.get(str(name), PALETTES[DEFAULT_PRESET])
        if not palette:
            return [(0, 0, 0), (255, 255, 255)]
        return [tuple(color) for color in palette]

    @classmethod
    def _palette_gradient(cls, name, invert, n_colors, use_log_scale):
        palette = cls._palette_data(name)
        if invert:
            palette = list(reversed(palette))
        colors = cls._sample_palette(palette, cls._sanitize_n_colors(n_colors))
        if len(colors) == 1:
            r, g, b = colors[0]
            return f"rgb({r}, {g}, {b})"

        stops = []
        for idx, (r, g, b) in enumerate(colors):
            if use_log_scale:
                offset = cls._log_offset(idx, len(colors))
            else:
                offset = (idx / (len(colors) - 1)) * 100.0
            stops.append(f"rgb({r}, {g}, {b}) {offset:.4f}%")
        return f"linear-gradient(90deg, {', '.join(stops)})"

    @staticmethod
    def _sample_palette(palette, n_colors):
        if n_colors <= 1:
            return [palette[0]]
        if len(palette) == 1:
            return [palette[0]] * n_colors

        max_idx = len(palette) - 1
        sampled = []
        for i in range(n_colors):
            t = (i / (n_colors - 1)) * max_idx
            lo = math.floor(t)
            hi = min(max_idx, lo + 1)
            frac = t - lo
            r = round((1 - frac) * palette[lo][0] + frac * palette[hi][0])
            g = round((1 - frac) * palette[lo][1] + frac * palette[hi][1])
            b = round((1 - frac) * palette[lo][2] + frac * palette[hi][2])
            sampled.append((r, g, b))
        return sampled

    @staticmethod
    def _log_offset(idx, count):
        if count <= 1:
            return 0.0
        linear = idx / (count - 1)
        return math.log10(1 + 9 * linear) * 100.0
