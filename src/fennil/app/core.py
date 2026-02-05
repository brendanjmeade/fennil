import os
from pathlib import Path

import numpy as np

# Import pydeck and trame-deckgl
import pydeck as pdk
from trame.app import TrameApp
from trame.decorators import change, controller
from trame.ui.vuetify3 import SinglePageLayout
from trame.widgets import html, vuetify3
from trame_deckgl.widgets import deckgl

from .data import is_valid_data_folder, load_folder_data
from .layers import build_layers_for_folder


def _load_mapbox_token():
    token = os.getenv("FENNIL_MAP_BOX_TOKEN")
    if token:
        return token
    # Fallback: read from a local .env if present
    for parent in Path(__file__).resolve().parents:
        env_file = parent / ".env"
        if env_file.is_file():
            for line in env_file.read_text().splitlines():
                if line.strip().startswith("FENNIL_MAP_BOX_TOKEN="):
                    return line.split("=", 1)[1].strip()
    return None


mapbox_access_token = _load_mapbox_token()
HAS_MAPBOX_TOKEN = bool(mapbox_access_token)


# ---------------------------------------------------------
# Constants
# ---------------------------------------------------------

VELOCITY_SCALE_MIN = 1.0e-6

FILE_BROWSER_HEADERS = [
    {"title": "Name", "align": "start", "key": "name", "sortable": False},
    {"title": "Type", "align": "start", "key": "type", "sortable": False},
]


class MyTrameApp(TrameApp):
    def __init__(self, server=None):
        super().__init__(server, client_type="vue3")

        # --hot-reload arg optional logic
        if self.server.hot_reload:
            self.server.controller.on_server_reload.add(self._build_ui)

        # Initialize state variables
        self.state.trame__title = "Earthquake Data Viewer"
        self.state.velocity_scale = 1.0
        self.state.velocity_scale_display = self._format_velocity_scale(
            self.state.velocity_scale
        )
        self.state.folder_1_path = "---"
        self.state.folder_2_path = "---"

        # Data storage
        self.folder_1_data = None
        self.folder_2_data = None

        # Visibility controls for folder 1
        self.state.show_locs_1 = False
        self.state.show_obs_1 = False
        self.state.show_mod_1 = False
        self.state.show_res_1 = False
        self.state.show_rot_1 = False
        self.state.show_seg_1 = False
        self.state.show_tri_1 = False
        self.state.show_str_1 = False
        self.state.show_mog_1 = False
        self.state.show_res_mag_1 = False
        self.state.show_seg_color_1 = False
        self.state.seg_slip_type_1 = "ss"
        self.state.show_tde_1 = False
        self.state.tde_slip_type_1 = "ss"
        self.state.show_fault_proj_1 = False

        # Visibility controls for folder 2
        self.state.show_locs_2 = False
        self.state.show_obs_2 = False
        self.state.show_mod_2 = False
        self.state.show_res_2 = False
        self.state.show_rot_2 = False
        self.state.show_seg_2 = False
        self.state.show_tri_2 = False
        self.state.show_str_2 = False
        self.state.show_mog_2 = False
        self.state.show_res_mag_2 = False
        self.state.show_seg_color_2 = False
        self.state.seg_slip_type_2 = "ss"
        self.state.show_tde_2 = False
        self.state.tde_slip_type_2 = "ss"
        self.state.show_fault_proj_2 = False

        # Shared controls
        self.state.show_res_compare = False

        # Map state
        self.state.map_latitude = 37.0
        self.state.map_longitude = -122.0
        self.state.map_zoom = 6
        self.state.map_pitch = 0
        self.state.map_bearing = 0

        # File browser state
        data_root = Path(__file__).parent.parent.parent.parent / "data"
        self.state.show_file_browser = False
        self.state.file_browser_target = 1
        self.state.file_browser_current = str(data_root.resolve())
        self.state.file_browser_listing = []
        self.state.file_browser_active = -1
        self.state.file_browser_error = ""
        self.state.file_browser_headers = FILE_BROWSER_HEADERS
        self.state.folder_1_full_path = ""
        self.state.folder_2_full_path = ""
        self.state.deckgl_tooltip = {
            "html": "{tooltip}",
            "style": {
                "backgroundColor": "rgba(0, 0, 0, 0.85)",
                "color": "white",
                "fontSize": "12px",
            },
        }

        # One-time registration guard
        self._ready_registered = False

        # build ui
        self._build_ui()

        # Initialize file browser listing
        self._file_browser_update_listing()

    def _initialize_map(self, **kwargs):  # noqa: ARG002
        """Initialize the map with default view"""
        self.ctrl.deck_update(self._build_deck([]))

    def _file_browser_update_listing(self):
        current = Path(self.state.file_browser_current)
        if not current.exists():
            current = Path.home()
            self.state.file_browser_current = str(current.resolve())
        entries = []
        for entry in current.iterdir():
            name = entry.name
            if name.startswith("."):
                continue
            if entry.is_dir():
                entries.append(
                    {
                        "name": name,
                        "type": "directory",
                        "icon": "mdi-folder",
                    }
                )
            elif entry.is_file():
                entries.append(
                    {
                        "name": name,
                        "type": "file",
                        "icon": "mdi-file-document-outline",
                    }
                )
        entries.sort(key=lambda item: (item["type"] != "directory", item["name"]))
        listing = [{**item, "index": idx} for idx, item in enumerate(entries)]
        with self.state:
            self.state.file_browser_listing = listing
            self.state.file_browser_active = -1

    def _file_browser_select_entry(self, entry):
        self.state.file_browser_active = entry.get("index", -1) if entry else -1

    def _file_browser_open_entry(self, entry):
        if not entry:
            return
        if entry.get("type") != "directory":
            return
        current = Path(self.state.file_browser_current)
        next_path = (current / entry.get("name")).resolve()
        self.state.file_browser_current = str(next_path)
        self._file_browser_update_listing()

    def _file_browser_go_home(self):
        self.state.file_browser_current = str(Path.home().resolve())
        self._file_browser_update_listing()

    def _file_browser_go_parent(self):
        current = Path(self.state.file_browser_current)
        parent = current.parent if current.parent != current else current
        self.state.file_browser_current = str(parent.resolve())
        self._file_browser_update_listing()

    def _file_browser_select_folder(self):
        current = Path(self.state.file_browser_current)
        folder_path = current
        active_idx = self.state.file_browser_active
        if active_idx is not None and active_idx >= 0:
            if active_idx >= len(self.state.file_browser_listing):
                active_idx = -1
            else:
                entry = self.state.file_browser_listing[active_idx]
                if entry.get("type") == "directory":
                    folder_path = (current / entry.get("name")).resolve()
        if not is_valid_data_folder(folder_path):
            self.state.file_browser_error = (
                "Selected folder is missing required model_*.csv files."
            )
            return
        self.state.file_browser_error = ""
        target = int(self.state.file_browser_target)
        self.state[f"folder_{target}_full_path"] = str(folder_path)
        self.state.show_file_browser = False
        self._load_data(target, folder_path=folder_path)

    def _open_file_browser(self, folder_number):
        self.state.file_browser_target = folder_number
        existing = getattr(self.state, f"folder_{folder_number}_full_path", "")
        if existing:
            self.state.file_browser_current = str(Path(existing).resolve())
        self.state.show_file_browser = True
        self.state.file_browser_error = ""
        self._file_browser_update_listing()

    def _load_data(self, folder_number, folder_path=None):
        """Load earthquake data from a folder"""
        base_path = Path(__file__).parent.parent.parent.parent / "data"
        if folder_path is None:
            stored = getattr(self.state, f"folder_{folder_number}_full_path", "")
            folder_path = Path(stored) if stored else None
        if folder_path is None:
            folder_path = base_path / "0000000157"
        folder_name = Path(folder_path)

        # Update folder display
        folder_path_var = f"folder_{folder_number}_path"
        self.state[folder_path_var] = folder_name.name
        self.state[f"folder_{folder_number}_full_path"] = str(folder_name.resolve())

        data = load_folder_data(folder_name)

        if folder_number == 1:
            self.folder_1_data = data
        else:
            self.folder_2_data = data

        # Update visualization
        self._update_layers()

        print(f"Loaded data from {folder_name}")  # noqa: T201

    @controller.set("load_folder_1")
    def load_folder_1(self):
        """Open file browser for folder 1"""
        self._open_file_browser(1)

    @controller.set("load_folder_2")
    def load_folder_2(self):
        """Open file browser for folder 2"""
        self._open_file_browser(2)

    def _update_layers(self):
        """Update DeckGL layers based on loaded data and visibility controls"""
        base_layers = []
        layers = []
        vector_layers = []

        # Process folder 1 data
        if self.folder_1_data is not None:
            tde_layers, folder_layers, folder_vectors = build_layers_for_folder(
                1, self.folder_1_data, self.state
            )
            base_layers.extend(tde_layers)
            layers.extend(folder_layers)
            vector_layers.extend(folder_vectors)

        # Process folder 2 data
        if self.folder_2_data is not None:
            tde_layers, folder_layers, folder_vectors = build_layers_for_folder(
                2, self.folder_2_data, self.state
            )
            base_layers.extend(tde_layers)
            layers.extend(folder_layers)
            vector_layers.extend(folder_vectors)

        self.ctrl.deck_update(self._build_deck(base_layers + layers + vector_layers))

    def _build_deck(self, layers):
        """Construct a Deck instance with current map settings and provided layers."""
        return pdk.Deck(
            map_provider="mapbox" if HAS_MAPBOX_TOKEN else "carto",
            map_style="mapbox://styles/mapbox/light-v9"
            if HAS_MAPBOX_TOKEN
            else pdk.map_styles.LIGHT,
            initial_view_state=pdk.ViewState(
                latitude=self.state.map_latitude,
                longitude=self.state.map_longitude,
                zoom=self.state.map_zoom,
                pitch=self.state.map_pitch,
                bearing=self.state.map_bearing,
            ),
            layers=layers,
        )

    @change("velocity_scale")
    def on_velocity_scale_change(self, velocity_scale, **kwargs):  # noqa: ARG002
        """Update velocity vector scaling"""
        try:
            value = float(velocity_scale)
        except (TypeError, ValueError):
            self.state.velocity_scale = 1.0
            self._update_layers()
            return
        if not np.isfinite(value):
            self.state.velocity_scale = 1.0
            self._update_layers()
            return
        if value < VELOCITY_SCALE_MIN:
            self.state.velocity_scale = VELOCITY_SCALE_MIN
        elif value != velocity_scale:
            self.state.velocity_scale = value
        self.state.velocity_scale_display = self._format_velocity_scale(
            self.state.velocity_scale
        )
        self._update_layers()

    @change("velocity_scale_display")
    def on_velocity_scale_display_change(self, velocity_scale_display, **kwargs):  # noqa: ARG002
        """Parse display text and update velocity scale."""
        if velocity_scale_display in (None, ""):
            return
        try:
            value = float(velocity_scale_display)
        except (TypeError, ValueError):
            return
        if not np.isfinite(value):
            return
        value = max(value, VELOCITY_SCALE_MIN)
        if abs(value - self.state.velocity_scale) < 1.0e-12:
            return
        self.state.velocity_scale = value

    def _set_velocity_scale(self, value):
        if value is None:
            return
        try:
            value = float(value)
        except (TypeError, ValueError):
            return
        if not np.isfinite(value):
            return
        self.state.velocity_scale = max(value, VELOCITY_SCALE_MIN)

    @staticmethod
    def _format_velocity_scale(value):
        text = f"{value:.6f}"
        text = text.rstrip("0").rstrip(".")
        return text or "0"

    @controller.set("velocity_scale_reset")
    def velocity_scale_reset(self):
        self._set_velocity_scale(1.0)

    @controller.set("velocity_scale_fine_down")
    def velocity_scale_fine_down(self):
        self._set_velocity_scale(self.state.velocity_scale * 0.9)

    @controller.set("velocity_scale_fine_up")
    def velocity_scale_fine_up(self):
        self._set_velocity_scale(self.state.velocity_scale * 1.1)

    @controller.set("velocity_scale_mag_down")
    def velocity_scale_mag_down(self):
        self._set_velocity_scale(self.state.velocity_scale / 2.0)

    @controller.set("velocity_scale_mag_up")
    def velocity_scale_mag_up(self):
        self._set_velocity_scale(self.state.velocity_scale * 2.0)

    @change(
        "show_locs_1",
        "show_obs_1",
        "show_mod_1",
        "show_res_1",
        "show_rot_1",
        "show_seg_1",
        "show_tri_1",
        "show_str_1",
        "show_mog_1",
        "show_seg_color_1",
        "seg_slip_type_1",
        "show_tde_1",
        "tde_slip_type_1",
        "show_fault_proj_1",
        "show_locs_2",
        "show_obs_2",
        "show_mod_2",
        "show_res_2",
        "show_rot_2",
        "show_seg_2",
        "show_tri_2",
        "show_str_2",
        "show_mog_2",
        "show_seg_color_2",
        "seg_slip_type_2",
        "show_tde_2",
        "tde_slip_type_2",
        "show_fault_proj_2",
    )
    def on_visibility_change(self, **kwargs):  # noqa: ARG002
        """Update visualization when visibility controls change"""
        self._update_layers()

    def _build_ui(self, *args, **kwargs):  # noqa: ARG002
        with SinglePageLayout(self.server) as self.ui:
            # Toolbar
            self.ui.title.set_text("Earthquake Data Viewer")

            # Main content - recreating Panel GridSpec layout
            with self.ui.content:
                with vuetify3.VContainer(
                    fluid=True, classes="pa-0 fill-height", style="max-height: 700px;"
                ):
                    # Main grid: controls area + large map area
                    with vuetify3.VRow(classes="fill-height", no_gutters=True):
                        # LEFT AREA - Controls (two columns + shared row)
                        with vuetify3.VCol(cols=3, classes="pa-0 d-flex flex-column"):
                            with vuetify3.VRow(classes="flex-grow-1", no_gutters=True):
                                # Folder 1 controls (left half)
                                with vuetify3.VCol(
                                    cols=6,
                                    classes="pa-2 d-flex flex-column",
                                    style="overflow-y: auto;",
                                ):
                                    # Row 0-1: Load button and velocity controls
                                    vuetify3.VBtn(
                                        "load",
                                        click=self.load_folder_1,
                                        color="success",
                                        block=True,
                                        size="small",
                                    )
                                    html.Div(
                                        "{{ folder_1_path }}",
                                        classes="text-caption mt-1 mb-2",
                                        style="font-size: 0.7rem;",
                                    )

                                    # Velocity checkboxes
                                    vuetify3.VCheckbox(
                                        v_model="show_locs_1",
                                        label="locs",
                                        hide_details=True,
                                        density="compact",
                                    )
                                    vuetify3.VCheckbox(
                                        v_model="show_obs_1",
                                        label="obs",
                                        hide_details=True,
                                        density="compact",
                                    )
                                    vuetify3.VCheckbox(
                                        v_model="show_mod_1",
                                        label="mod",
                                        hide_details=True,
                                        density="compact",
                                    )
                                    vuetify3.VCheckbox(
                                        v_model="show_res_1",
                                        label="res",
                                        hide_details=True,
                                        density="compact",
                                    )
                                    vuetify3.VCheckbox(
                                        v_model="show_rot_1",
                                        label="rot",
                                        hide_details=True,
                                        density="compact",
                                    )
                                    vuetify3.VCheckbox(
                                        v_model="show_seg_1",
                                        label="seg",
                                        hide_details=True,
                                        density="compact",
                                    )
                                    vuetify3.VCheckbox(
                                        v_model="show_tri_1",
                                        label="tri",
                                        hide_details=True,
                                        density="compact",
                                    )
                                    vuetify3.VCheckbox(
                                        v_model="show_str_1",
                                        label="str",
                                        hide_details=True,
                                        density="compact",
                                    )
                                    vuetify3.VCheckbox(
                                        v_model="show_mog_1",
                                        label="mog",
                                        hide_details=True,
                                        density="compact",
                                    )
                                    vuetify3.VCheckbox(
                                        v_model="show_res_mag_1",
                                        label="res mag",
                                        hide_details=True,
                                        density="compact",
                                    )

                                    vuetify3.VDivider(classes="my-2")

                                    # Row 6: Segment/TDE color controls
                                    vuetify3.VCheckbox(
                                        v_model="show_seg_color_1",
                                        label="slip",
                                        hide_details=True,
                                        density="compact",
                                    )
                                    with vuetify3.VBtnToggle(
                                        v_model="seg_slip_type_1",
                                        mandatory=True,
                                        density="compact",
                                        divided=True,
                                    ):
                                        vuetify3.VBtn("ss", value="ss", size="x-small")
                                        vuetify3.VBtn("ds", value="ds", size="x-small")

                                    vuetify3.VCheckbox(
                                        v_model="show_tde_1",
                                        label="tde",
                                        hide_details=True,
                                        density="compact",
                                    )
                                    with vuetify3.VBtnToggle(
                                        v_model="tde_slip_type_1",
                                        mandatory=True,
                                        density="compact",
                                        divided=True,
                                    ):
                                        vuetify3.VBtn("ss", value="ss", size="x-small")
                                        vuetify3.VBtn("ds", value="ds", size="x-small")

                                    vuetify3.VCheckbox(
                                        v_model="show_fault_proj_1",
                                        label="fault proj",
                                        hide_details=True,
                                        density="compact",
                                    )

                                # Folder 2 controls (right half)
                                with vuetify3.VCol(
                                    cols=6,
                                    classes="pa-2 d-flex flex-column",
                                    style="overflow-y: auto;",
                                ):
                                    # Row 0-1: Load button and velocity controls
                                    vuetify3.VBtn(
                                        "load",
                                        click=self.load_folder_2,
                                        color="success",
                                        block=True,
                                        size="small",
                                    )
                                    html.Div(
                                        "{{ folder_2_path }}",
                                        classes="text-caption mt-1 mb-2",
                                        style="font-size: 0.7rem;",
                                    )

                                    # Velocity checkboxes
                                    vuetify3.VCheckbox(
                                        v_model="show_locs_2",
                                        label="locs",
                                        hide_details=True,
                                        density="compact",
                                    )
                                    vuetify3.VCheckbox(
                                        v_model="show_obs_2",
                                        label="obs",
                                        hide_details=True,
                                        density="compact",
                                    )
                                    vuetify3.VCheckbox(
                                        v_model="show_mod_2",
                                        label="mod",
                                        hide_details=True,
                                        density="compact",
                                    )
                                    vuetify3.VCheckbox(
                                        v_model="show_res_2",
                                        label="res",
                                        hide_details=True,
                                        density="compact",
                                    )
                                    vuetify3.VCheckbox(
                                        v_model="show_rot_2",
                                        label="rot",
                                        hide_details=True,
                                        density="compact",
                                    )
                                    vuetify3.VCheckbox(
                                        v_model="show_seg_2",
                                        label="seg",
                                        hide_details=True,
                                        density="compact",
                                    )
                                    vuetify3.VCheckbox(
                                        v_model="show_tri_2",
                                        label="tri",
                                        hide_details=True,
                                        density="compact",
                                    )
                                    vuetify3.VCheckbox(
                                        v_model="show_str_2",
                                        label="str",
                                        hide_details=True,
                                        density="compact",
                                    )
                                    vuetify3.VCheckbox(
                                        v_model="show_mog_2",
                                        label="mog",
                                        hide_details=True,
                                        density="compact",
                                    )
                                    vuetify3.VCheckbox(
                                        v_model="show_res_mag_2",
                                        label="res mag",
                                        hide_details=True,
                                        density="compact",
                                    )

                                    vuetify3.VDivider(classes="my-2")

                                    # Row 6: Segment/TDE color controls
                                    vuetify3.VCheckbox(
                                        v_model="show_seg_color_2",
                                        label="slip",
                                        hide_details=True,
                                        density="compact",
                                    )
                                    with vuetify3.VBtnToggle(
                                        v_model="seg_slip_type_2",
                                        mandatory=True,
                                        density="compact",
                                        divided=True,
                                    ):
                                        vuetify3.VBtn("ss", value="ss", size="x-small")
                                        vuetify3.VBtn("ds", value="ds", size="x-small")

                                    vuetify3.VCheckbox(
                                        v_model="show_tde_2",
                                        label="tde",
                                        hide_details=True,
                                        density="compact",
                                    )
                                    with vuetify3.VBtnToggle(
                                        v_model="tde_slip_type_2",
                                        mandatory=True,
                                        density="compact",
                                        divided=True,
                                    ):
                                        vuetify3.VBtn("ss", value="ss", size="x-small")
                                        vuetify3.VBtn("ds", value="ds", size="x-small")

                                    vuetify3.VCheckbox(
                                        v_model="show_fault_proj_2",
                                        label="fault proj",
                                        hide_details=True,
                                        density="compact",
                                    )

                            vuetify3.VDivider(classes="my-1")

                            # Shared controls row (full width of controls area)
                            with html.Div(classes="pa-2"):
                                vuetify3.VCheckbox(
                                    v_model="show_res_compare",
                                    label="res compare",
                                    hide_details=True,
                                    density="compact",
                                )
                                html.Div(
                                    "vel scale",
                                    classes="text-caption mt-1",
                                    style="font-size: 0.7rem;",
                                )
                                with html.Div(classes="d-flex flex-wrap ga-1 mt-1"):
                                    vuetify3.VBtn(
                                        "90%",
                                        click=self.velocity_scale_fine_down,
                                        size="x-small",
                                        variant="outlined",
                                    )
                                    vuetify3.VBtn(
                                        "/2",
                                        click=self.velocity_scale_mag_down,
                                        size="x-small",
                                        variant="outlined",
                                    )
                                    vuetify3.VBtn(
                                        "1:1",
                                        click=self.velocity_scale_reset,
                                        size="x-small",
                                        variant="outlined",
                                    )
                                    vuetify3.VBtn(
                                        "x2",
                                        click=self.velocity_scale_mag_up,
                                        size="x-small",
                                        variant="outlined",
                                    )
                                    vuetify3.VBtn(
                                        "110%",
                                        click=self.velocity_scale_fine_up,
                                        size="x-small",
                                        variant="outlined",
                                    )
                                vuetify3.VTextField(
                                    v_model=("velocity_scale_display", "1"),
                                    label="scale",
                                    type="text",
                                    inputmode="decimal",
                                    density="compact",
                                    hide_details=True,
                                    variant="outlined",
                                    classes="mt-1",
                                )

                        # RIGHT LARGE AREA - Map and Colorbars
                        with vuetify3.VCol(cols=9, classes="pa-0 d-flex flex-column"):
                            # Main map area (rows 0-8)
                            with vuetify3.VCard(
                                classes="flex-grow-1",
                                style="min-height: 0; position: relative;",
                            ):
                                # DeckGL Map
                                deck_map = deckgl.Deck(
                                    mapbox_api_key=mapbox_access_token
                                    if HAS_MAPBOX_TOKEN
                                    else "",
                                    tooltip=("deckgl_tooltip", None),
                                    style="width: 100%; height: 100%;",
                                    classes="fill-height",
                                )
                                self.ctrl.deck_update = deck_map.update

                                # Initialize map after UI is built
                                if not self._ready_registered:
                                    self.server.controller.on_server_ready.add(
                                        self._initialize_map
                                    )
                                    self._ready_registered = True

                            # Colorbar area (row 8)
                            with vuetify3.VCard(
                                classes="pa-2 d-flex justify-space-around align-center",
                                height="50",
                                flat=True,
                            ):
                                # Slip rate colorbar placeholder
                                html.Div(
                                    "Slip rate (mm/yr): -100 ←→ +100",
                                    style="font-size: 0.75rem; color: #666;",
                                )
                                # Residual magnitude colorbar placeholder
                                html.Div(
                                    "Resid. mag. (mm/yr): 0 → 5",
                                    style="font-size: 0.75rem; color: #666;",
                                )
                                # Residual diff colorbar placeholder
                                html.Div(
                                    "Resid. diff. (mm/yr): -5 ←→ +5",
                                    style="font-size: 0.75rem; color: #666;",
                                )

                with vuetify3.VDialog(
                    v_model=("show_file_browser", False),
                    max_width="900",
                    persistent=True,
                ):
                    with vuetify3.VCard(title="Select data folder", rounded="lg"):
                        with vuetify3.VCardText():
                            with vuetify3.VRow(dense=True, classes="align-center"):
                                vuetify3.VBtn(
                                    icon="mdi-home",
                                    variant="text",
                                    size="small",
                                    click=self._file_browser_go_home,
                                )
                                vuetify3.VBtn(
                                    icon="mdi-folder-upload-outline",
                                    variant="text",
                                    size="small",
                                    click=self._file_browser_go_parent,
                                )
                                vuetify3.VTextField(
                                    v_model=("file_browser_current", ""),
                                    hide_details=True,
                                    density="compact",
                                    variant="outlined",
                                    readonly=True,
                                    classes="ml-2 flex-grow-1",
                                )
                            with vuetify3.VDataTable(
                                density="compact",
                                fixed_header=True,
                                headers=("file_browser_headers", FILE_BROWSER_HEADERS),
                                items=("file_browser_listing", []),
                                height="50vh",
                                style="user-select: none; cursor: pointer;",
                                items_per_page=-1,
                            ):
                                vuetify3.Template(raw_attrs=["v-slot:bottom"])
                                with vuetify3.Template(
                                    raw_attrs=['v-slot:item="{ item }"']
                                ):
                                    with vuetify3.VDataTableRow(
                                        item=("item",),
                                        click=(
                                            self._file_browser_select_entry,
                                            "[item]",
                                        ),
                                        dblclick=(
                                            self._file_browser_open_entry,
                                            "[item]",
                                        ),
                                        classes=(
                                            "{ 'bg-grey-lighten-3': item.index === file_browser_active }",
                                        ),
                                    ):
                                        with vuetify3.Template(
                                            raw_attrs=["v-slot:item.name"]
                                        ):
                                            with html.Div(
                                                classes="d-flex align-center"
                                            ):
                                                vuetify3.VIcon(
                                                    "{{ item.icon }}",
                                                    size="small",
                                                    classes="mr-2",
                                                )
                                                html.Div("{{ item.name }}")
                                        with vuetify3.Template(
                                            raw_attrs=["v-slot:item.type"]
                                        ):
                                            html.Div("{{ item.type }}")

                        with vuetify3.VCardActions(classes="pa-3"):
                            html.Div(
                                "{{ file_browser_error }}",
                                v_if="file_browser_error",
                                classes="text-error text-caption",
                            )
                            vuetify3.VSpacer()
                            vuetify3.VBtn(
                                text="Cancel",
                                variant="flat",
                                click="show_file_browser=false",
                            )
                            vuetify3.VBtn(
                                text="Select folder",
                                color="primary",
                                variant="flat",
                                click=self._file_browser_select_folder,
                            )
