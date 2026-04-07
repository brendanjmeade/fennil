from trame.widgets import html
from trame.widgets import vuetify3 as v3

from fennil.app.viz.colormaps import (
    DEFAULT_COLORMAP_NAME,
    DEFAULT_N_COLORS,
    palette_gradient_css,
    parse_colormap_range,
)


class Footer:
    def __init__(self, app, datasets):
        self._app = app
        self._state = app.state
        self._datasets = datasets
        self._state.footer_colormaps = []

    def build_entries(self, specs):
        entries = []
        for field_name in sorted(
            specs.keys(),
            key=lambda name: specs.get(name, {}).get("priority", 999),
        ):
            spec = specs.get(field_name, {})
            styles = spec.get("styles") or {}
            color_map_range = styles.get("color_map_range")
            if not isinstance(color_map_range, dict):
                continue
            if not self._field_has_active_dataset(field_name):
                continue

            parsed = parse_colormap_range(
                color_map_range,
                default_min=color_map_range.get("min", 0.0),
                default_max=color_map_range.get("max", 1.0),
                default_palette=color_map_range.get("palette", DEFAULT_COLORMAP_NAME),
                default_n_colors=color_map_range.get("n_colors", DEFAULT_N_COLORS),
            )
            entries.append(
                {
                    "name": field_name,
                    "label": spec.get("label", field_name),
                    "min_label": self._format_value(parsed["min"]),
                    "max_label": self._format_value(parsed["max"]),
                    "gradient": palette_gradient_css(
                        parsed["palette"],
                        n_colors=parsed["n_colors"],
                        invert=parsed["invert"],
                        use_log_scale=parsed["use_log_scale"],
                    ),
                }
            )
        return entries

    def build_ui(self):
        with v3.VFooter(app=True, height="auto", classes="pa-2"):
            with html.Div(classes="d-flex flex-wrap align-center ga-4 w-100"):
                with html.Div(
                    v_for="entry in footer_colormaps",
                    key="entry.name",
                    classes="d-flex align-center ga-2",
                ):
                    html.Div(
                        "{{ entry.label }}:",
                        classes="text-caption text-no-wrap",
                    )
                    html.Div(
                        "{{ entry.min_label }}",
                        classes="text-caption text-no-wrap",
                    )
                    html.Div(
                        style=[
                            "`width:140px;height:10px;border:1px solid #666;border-radius:4px;background:${entry.gradient};`"
                        ],
                    )
                    html.Div(
                        "{{ entry.max_label }}",
                        classes="text-caption text-no-wrap",
                    )
                html.Div(
                    "No active color maps",
                    v_if="!footer_colormaps.length",
                    classes="text-caption text-medium-emphasis",
                )
                if self._app.server.hot_reload:
                    v3.VSpacer()
                    v3.VBtn(
                        icon="mdi-refresh",
                        click=self._app.ctrl.on_server_reload,
                        density="compact",
                        classes="rounded",
                        flat=True,
                    )

    def _field_has_active_dataset(self, field_name):
        for dataset in self._datasets:
            if not dataset.enabled:
                continue
            if field_name not in dataset.available_fields:
                continue
            if dataset.fields.get(field_name):
                return True
        return False

    @staticmethod
    def _format_value(value):
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return str(value)
        if parsed.is_integer():
            return str(int(parsed))
        return f"{parsed:.4g}"
