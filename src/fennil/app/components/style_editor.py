import copy

from trame.widgets import html
from trame.widgets import vuetify3 as v3

from fennil.app.viz.styles import RDBU_11, normalize_dataset_values

PALETTES = {
    "RDBU_11": RDBU_11,
}
DEFAULT_PICKER_HEXA = "#000000ff"
PICKER_STATE_KEYS = (
    "style_editor_picker_open",
    "style_editor_picker_hexa",
    "style_editor_picker_field_idx",
    "style_editor_picker_group_idx",
    "style_editor_picker_entry_idx",
)
COLOR_STYLE_GROUPS = (
    ("colors", "Color"),
    ("fill", "Fill"),
    ("line", "Line"),
)
DATASET_GRID_STYLE = "`display:grid;grid-template-columns:repeat(${group.values.length}, minmax(0, 1fr));`"
DATASET_CARD_STYLE = "border: 1px solid rgba(127,127,127,0.35); border-radius: 8px;"
COLOR_SWATCH_STYLE = "`width:32px;height:32px;min-width:32px;border-radius:50%;border:1px solid #666;background:${entry.hexa};`"
COLORMAP_BAR_STYLE = "`height: 14px; border: 1px solid #666; border-radius: 4px; background: ${group.gradient};`"
MINMAX_GRID_STYLE = "display:grid;grid-template-columns:minmax(0, 1fr) minmax(0, 1fr);"


class StyleEditor:
    def __init__(self, app, datasets):
        self._state = app.state
        self._datasets = datasets
        self._init_state()

    def _init_state(self):
        # Keep large editable form state client-side to avoid server echo jitter
        # while users type in text fields.
        for key in ("style_editor_controls", *PICKER_STATE_KEYS):
            self._state.client_only(key)
        self._state.show_style_editor = False
        self._state.style_editor_controls = []
        self._state.style_editor_picker_open = False
        self._state.style_editor_picker_hexa = DEFAULT_PICKER_HEXA
        self._state.style_editor_picker_field_idx = -1
        self._state.style_editor_picker_group_idx = -1
        self._state.style_editor_picker_entry_idx = -1
        self._state.style_editor_error = ""

    def build_ui(self):
        with v3.VNavigationDrawer(
            location="right",
            temporary=True,
            width=560,
            v_model=("show_style_editor", False),
        ):
            with v3.VToolbar(density="compact", flat=True):
                v3.VToolbarTitle("Style Editor")
                v3.VSpacer()
                v3.VBtn(
                    icon="mdi-close",
                    variant="text",
                    click="show_style_editor = false",
                )

            with v3.VContainer(classes="pa-3"):
                with v3.VExpansionPanels(multiple=True):
                    with v3.VExpansionPanel(
                        v_for="(field, field_idx) in style_editor_controls",
                        key="field.name",
                    ):
                        with v3.VExpansionPanelTitle():
                            with html.Div(classes="d-flex align-center ga-2"):
                                v3.VIcon(
                                    icon=["field.icon"],
                                    color=["field.icon_color || undefined"],
                                    size="small",
                                )
                                html.Div("{{ field.label }}", classes="text-subtitle-2")
                        with v3.VExpansionPanelText():
                            with html.Div(
                                v_for="(group, group_idx) in field.color_groups",
                                key="group.key",
                                classes="mb-2",
                            ):
                                html.Div(
                                    "{{ group.label }}", classes="text-caption mb-1"
                                )
                                with html.Div(
                                    classes="ga-3",
                                    style=[DATASET_GRID_STYLE],
                                ):
                                    with html.Div(
                                        v_for="(entry, entry_idx) in group.values",
                                        key="entry.idx",
                                        classes="pa-2",
                                        style=DATASET_CARD_STYLE,
                                    ):
                                        html.Div(
                                            "{{ entry.label }}",
                                            classes="text-caption mb-2",
                                        )
                                        with html.Div(
                                            classes="d-flex align-center ga-2"
                                        ):
                                            v3.VBtn(
                                                "",
                                                variant="flat",
                                                density="compact",
                                                size="small",
                                                style=[COLOR_SWATCH_STYLE],
                                                click=self._open_picker_js(),
                                            )
                                            v3.VTextField(
                                                v_model="entry.hexa",
                                                label="HEXA",
                                                density="compact",
                                                hide_details=True,
                                                variant="outlined",
                                                style="min-width: 0; flex: 1 1 auto;",
                                            )
                            with html.Div(
                                v_for="group in field.width_groups",
                                key="group.key",
                                classes="mb-2",
                            ):
                                html.Div(
                                    "{{ group.label }}", classes="text-caption mb-1"
                                )
                                with html.Div(
                                    classes="ga-3",
                                    style=[DATASET_GRID_STYLE],
                                ):
                                    with html.Div(
                                        v_for="entry in group.values",
                                        key="entry.idx",
                                        classes="pa-2",
                                        style=DATASET_CARD_STYLE,
                                    ):
                                        html.Div(
                                            "{{ entry.label }}",
                                            classes="text-caption mb-2",
                                        )
                                        v3.VNumberInput(
                                            v_model="entry.value",
                                            label="Line Width",
                                            density="compact",
                                            hide_details=True,
                                            variant="outlined",
                                            control_variant="split",
                                            style="min-width: 0;",
                                        )
                            with html.Div(
                                v_for="group in field.colormap_groups",
                                key="group.key",
                                classes="mb-2",
                            ):
                                html.Div(
                                    "{{ group.label }}", classes="text-caption mb-1"
                                )
                                html.Div(
                                    classes="mb-2",
                                    style=[COLORMAP_BAR_STYLE],
                                )
                                with html.Div(
                                    classes="ga-3",
                                    style=MINMAX_GRID_STYLE,
                                ):
                                    v3.VNumberInput(
                                        v_model="group.min",
                                        label="Min",
                                        density="compact",
                                        hide_details=True,
                                        variant="outlined",
                                        control_variant="split",
                                        style="min-width: 0;",
                                    )
                                    v3.VNumberInput(
                                        v_model="group.max",
                                        label="Max",
                                        density="compact",
                                        hide_details=True,
                                        variant="outlined",
                                        control_variant="split",
                                        style="min-width: 0;",
                                    )
                            html.Div(
                                "No editable styles.",
                                v_if="!field.color_groups.length && !field.width_groups.length && !field.colormap_groups.length",
                                classes="text-caption text-medium-emphasis",
                            )
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
                                update_modelValue=self._picker_update_js(),
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
                html.Div(
                    "{{ style_editor_error }}",
                    v_if="style_editor_error",
                    classes="text-error text-caption mt-2",
                )
                with html.Div(classes="d-flex justify-end mt-3"):
                    v3.VBtn(
                        "Apply Styles",
                        color="primary",
                        click=(self.apply_all, "[style_editor_controls]"),
                        disabled=("style_editor_controls.length === 0",),
                        size="large",
                    )

    def open(self):
        self.refresh()
        self._state.show_style_editor = True

    def refresh(self):
        with self._state:
            self._state.style_editor_controls = self._build_controls(
                self._state.field_specs
            )
            self._state.style_editor_error = ""

    def apply_all(self, controls):
        controls = controls or []
        updated_specs = copy.deepcopy(self._state.field_specs)

        for field_control in controls:
            field_name = field_control.get("name", "")
            if field_name not in updated_specs:
                self._state.style_editor_error = f"Unknown field '{field_name}'."
                return
            styles = copy.deepcopy(updated_specs[field_name].get("styles") or {})

            if not self._apply_dataset_groups(
                styles,
                field_name,
                field_control.get("color_groups", []),
                self._parse_color_entry,
            ):
                return
            if not self._apply_dataset_groups(
                styles,
                field_name,
                field_control.get("width_groups", []),
                self._parse_width_entry,
            ):
                return
            if not self._apply_colormap_groups(styles, field_control, field_name):
                return

            updated_specs[field_name]["styles"] = styles

        with self._state:
            self._state.field_specs = updated_specs
            self._state.style_editor_error = ""

    def _build_controls(self, specs):
        controls = []
        columns = self._dataset_columns()
        for field_name in sorted(
            specs.keys(),
            key=lambda name: specs.get(name, {}).get("priority", 999),
        ):
            spec = specs.get(field_name, {})
            styles = spec.get("styles") or {}
            color_groups = self._build_color_groups(styles, columns)
            width_groups = self._build_width_groups(styles, columns)
            colormap_groups = self._build_colormap_groups(styles)

            controls.append(
                {
                    "name": field_name,
                    "label": spec.get("label", field_name),
                    "icon": spec.get("icon", "mdi-cog"),
                    "icon_color": styles.get("icon_color"),
                    "color_groups": color_groups,
                    "width_groups": width_groups,
                    "colormap_groups": colormap_groups,
                }
            )

        return controls

    def _dataset_columns(self):
        right = self._datasets[0]
        left = self._datasets[1]
        right_label = right.name if right.enabled and right.name else "Right"
        left_label = left.name if left.enabled and left.name else "Left"
        if left.enabled:
            # Match the main table ordering: left column first, right column second.
            return [(1, left_label), (0, right_label)]
        return [(0, right_label)]

    def _apply_dataset_groups(self, styles, field_name, groups, value_parser):
        for group in groups:
            key = group.get("key")
            if key not in styles:
                continue
            values = normalize_dataset_values(styles.get(key), styles.get(key))
            for entry in group.get("values", []):
                idx = self._entry_index(entry)
                if idx is None:
                    continue
                try:
                    values[idx] = value_parser(entry)
                except ValueError as exc:
                    self._state.style_editor_error = f"{field_name}.{key}[{idx}] {exc}"
                    return False
            styles[key] = values
        return True

    def _apply_colormap_groups(self, styles, field_control, field_name):
        for group in field_control.get("colormap_groups", []):
            key = group.get("key")
            if key not in styles:
                continue
            try:
                value_min = float(group.get("min"))
                value_max = float(group.get("max"))
            except (TypeError, ValueError):
                self._state.style_editor_error = (
                    f"{field_name}.{key} min/max must be numeric."
                )
                return False
            if value_min >= value_max:
                self._state.style_editor_error = (
                    f"{field_name}.{key} min must be less than max."
                )
                return False
            current = styles.get(key)
            updated = dict(current) if isinstance(current, dict) else {}
            if "palette" not in updated:
                updated["palette"] = "RDBU_11"
            updated["min"] = value_min
            updated["max"] = value_max
            styles[key] = updated
        return True

    def _build_color_groups(self, styles, columns):
        groups = []
        for key, label in COLOR_STYLE_GROUPS:
            group = self._build_dataset_group(
                styles,
                key=key,
                label=label,
                columns=columns,
                value_key="hexa",
                formatter=self._rgba_to_hexa,
            )
            if group is not None:
                groups.append(group)
        return groups

    def _build_width_groups(self, styles, columns):
        group = self._build_dataset_group(
            styles,
            key="line_width",
            label="Line width",
            columns=columns,
            value_key="value",
            formatter=self._to_float,
        )
        return [] if group is None else [group]

    def _build_colormap_groups(self, styles):
        color_map_range = styles.get("color_map_range")
        if not isinstance(color_map_range, dict):
            return []
        try:
            value_min = float(color_map_range.get("min"))
            value_max = float(color_map_range.get("max"))
        except (TypeError, ValueError):
            return []
        palette_name = str(color_map_range.get("palette", "RDBU_11"))
        return [
            {
                "key": "color_map_range",
                "label": "Color map range",
                "gradient": self._palette_gradient(palette_name),
                "min": value_min,
                "max": value_max,
            }
        ]

    def _build_dataset_group(self, styles, key, label, columns, value_key, formatter):
        value = styles.get(key)
        if not isinstance(value, list | tuple):
            return None
        pair = normalize_dataset_values(value, value)
        return {
            "key": key,
            "label": label,
            "values": self._build_dataset_entries(pair, columns, value_key, formatter),
        }

    @staticmethod
    def _build_dataset_entries(pair, columns, value_key, formatter):
        return [
            {
                "idx": idx,
                "label": column_label,
                value_key: formatter(pair[idx]),
            }
            for idx, column_label in columns
        ]

    @staticmethod
    def _entry_index(entry):
        try:
            idx = int(entry.get("idx", -1))
        except (TypeError, ValueError):
            return None
        return idx if idx in (0, 1) else None

    @staticmethod
    def _open_picker_js():
        return (
            "style_editor_picker_open = true;"
            "style_editor_picker_field_idx = field_idx;"
            "style_editor_picker_group_idx = group_idx;"
            "style_editor_picker_entry_idx = entry_idx;"
            "style_editor_picker_hexa = entry.hexa;"
        )

    @staticmethod
    def _picker_update_js():
        return """
(value) => {{
  style_editor_picker_hexa = value;
  const field = style_editor_controls?.[style_editor_picker_field_idx];
  const group = field?.color_groups?.[style_editor_picker_group_idx];
  const entry = group?.values?.[style_editor_picker_entry_idx];
  if (entry) {{
    entry.hexa = value;
  }}
}}
        """

    def _parse_color_entry(self, entry):
        return self._parse_color(entry.get("hexa", "#000000ff"))

    @staticmethod
    def _parse_width_entry(entry):
        try:
            return float(entry.get("value", "0"))
        except (TypeError, ValueError) as exc:
            msg = "must be numeric."
            raise ValueError(msg) from exc

    @staticmethod
    def _to_float(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

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
    def _palette_gradient(palette_name):
        palette = PALETTES.get(palette_name, RDBU_11)
        if not palette:
            return "linear-gradient(90deg, #000000, #ffffff)"
        if len(palette) == 1:
            r, g, b = palette[0]
            return f"rgb({r}, {g}, {b})"
        stop_count = len(palette) - 1
        stops = []
        for idx, (r, g, b) in enumerate(palette):
            pct = round((idx / stop_count) * 100)
            stops.append(f"rgb({r}, {g}, {b}) {pct}%")
        return f"linear-gradient(90deg, {', '.join(stops)})"
