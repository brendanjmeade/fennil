import os
from pathlib import Path

import numpy as np
import pandas as pd

# Import pydeck and trame-deckgl
import pydeck as pdk
from trame.app import TrameApp
from trame.decorators import change, controller
from trame.ui.vuetify3 import SinglePageLayout
from trame.widgets import html, vuetify3
from trame_deckgl.widgets import deckgl


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

VELOCITY_SCALE = 1000
VELOCITY_SCALE_MIN = 1.0e-6
KM2M = 1.0e3
RADIUS_EARTH = 6371000

# Per-layer colors (RGBA) and per-folder line widths, mirroring the legacy viewer
TYPE_COLORS = {
    1: {
        "obs": [0, 0, 205, 255],
        "mod": [205, 0, 0, 200],
        "res": [205, 0, 205, 200],
        "rot": [0, 205, 0, 200],
        "seg": [0, 205, 205, 200],
        "tde": [205, 133, 0, 200],
        "str": [0, 128, 128, 200],
        "mog": [128, 128, 128, 200],
        "loc": [0, 0, 0, 220],
    },
    2: {
        "obs": [0, 0, 205, 255],
        "mod": [205, 0, 0, 200],
        "res": [205, 0, 205, 200],
        "rot": [0, 205, 0, 200],
        "seg": [0, 205, 205, 200],
        "tde": [205, 133, 0, 200],
        "str": [0, 102, 102, 200],
        "mog": [102, 102, 102, 200],
        "loc": [0, 0, 0, 220],
    },
}

LINE_WIDTHS = {1: 1, 2: 2}

# ColorBrewer RdBu[11] palette for discrete slip-rate coloring
RDBU_11 = [
    (103, 0, 31),
    (178, 24, 43),
    (214, 96, 77),
    (244, 165, 130),
    (253, 219, 199),
    (247, 247, 247),
    (209, 229, 240),
    (146, 197, 222),
    (67, 147, 195),
    (33, 102, 172),
    (5, 48, 97),
]

SLIP_RATE_MIN = -100.0
SLIP_RATE_MAX = 100.0
SHIFT_LON = -360.0

FAULT_PROJ_STYLE = {
    1: {
        "fill": [173, 216, 230, 77],  # lightblue @ 0.3 alpha
        "line": [0, 0, 255, 255],  # blue
    },
    2: {
        "fill": [144, 238, 144, 77],  # lightgreen @ 0.3 alpha
        "line": [0, 128, 0, 255],  # green
    },
}

FAULT_LINE_STYLE = {
    1: {"color": [0, 0, 255, 255], "width": 1},
    2: {"color": [0, 128, 0, 255], "width": 3},
}

FILE_BROWSER_HEADERS = [
    {"title": "Name", "align": "start", "key": "name", "sortable": False},
    {"title": "Type", "align": "start", "key": "type", "sortable": False},
]


# ---------------------------------------------------------
# Coordinate transformation utilities
# ---------------------------------------------------------


def wgs84_to_web_mercator(lon, lat):
    """Converts decimal (longitude, latitude) to Web Mercator (x, y)"""
    EARTH_RADIUS = 6378137.0  # Earth's radius (m)
    x = EARTH_RADIUS * np.deg2rad(lon)
    y = EARTH_RADIUS * np.log(np.tan(np.pi / 4.0 + np.deg2rad(lat) / 2.0))
    return x, y


def web_mercator_to_wgs84(x, y):
    """Converts Web Mercator (x, y) to WGS84 (longitude, latitude)"""
    EARTH_RADIUS = 6378137.0  # Earth's radius (m)
    lon = np.rad2deg(x / EARTH_RADIUS)
    lat = np.rad2deg(2.0 * np.arctan(np.exp(y / EARTH_RADIUS)) - np.pi / 2.0)
    return lon, lat


# TODO: this may not be needed
def normalize_longitude_difference(start_lon, end_lon):
    """
    Normalize end longitude to be in the same 360-degree range as start longitude.
    This prevents vectors from wrapping around the world when crossing the date line.
    """
    # Calculate the difference
    diff = end_lon - start_lon

    # If the difference is > 180, we've wrapped around (going the long way)
    # Adjust by 360 to go the short way
    diff = np.where(diff > 180, diff - 360, diff)
    diff = np.where(diff < -180, diff + 360, diff)

    # Return the normalized end longitude
    return start_lon + diff


def wrap2360(lon):
    """Wrap longitude to 0-360 range"""
    lon[np.where(lon < 0.0)] += 360.0
    return lon


def calculate_fault_bottom_edge(lon1, lat1, lon2, lat2, depth_km, dip_degrees):
    """Calculate bottom edge coordinates for a dipping fault plane."""
    dip_rad = np.radians(dip_degrees)
    lat1_rad = np.radians(lat1)
    lat2_rad = np.radians(lat2)
    lon1_rad = np.radians(lon1)
    lon2_rad = np.radians(lon2)

    # Earth radius in kilometers
    earth_radius_km = 6371.0

    # For a vertical fault, bottom coordinates are the same as top
    if np.abs(dip_degrees - 90.0) < 1e-6:
        return lon1, lat1, lon2, lat2

    delta_lon = lon2_rad - lon1_rad
    y = np.sin(delta_lon) * np.cos(lat2_rad)
    x = np.cos(lat1_rad) * np.sin(lat2_rad) - np.sin(lat1_rad) * np.cos(
        lat2_rad
    ) * np.cos(delta_lon)
    strike_bearing = np.arctan2(y, x)

    # Dip direction is perpendicular to strike
    dip_direction = strike_bearing + np.pi / 2

    min_dip_rad = np.deg2rad(0.1)
    if np.abs(dip_rad) < min_dip_rad:
        return lon1, lat1, lon2, lat2

    horizontal_distance_km = depth_km / np.tan(dip_rad)
    angular_distance = horizontal_distance_km / earth_radius_km

    lat1_bottom_rad = np.arcsin(
        np.sin(lat1_rad) * np.cos(angular_distance)
        + np.cos(lat1_rad) * np.sin(angular_distance) * np.cos(dip_direction)
    )
    lon1_bottom_rad = lon1_rad + np.arctan2(
        np.sin(dip_direction) * np.sin(angular_distance) * np.cos(lat1_rad),
        np.cos(angular_distance) - np.sin(lat1_rad) * np.sin(lat1_bottom_rad),
    )

    lat2_bottom_rad = np.arcsin(
        np.sin(lat2_rad) * np.cos(angular_distance)
        + np.cos(lat2_rad) * np.sin(angular_distance) * np.cos(dip_direction)
    )
    lon2_bottom_rad = lon2_rad + np.arctan2(
        np.sin(dip_direction) * np.sin(angular_distance) * np.cos(lat2_rad),
        np.cos(angular_distance) - np.sin(lat2_rad) * np.sin(lat2_bottom_rad),
    )

    lon1_bottom = np.degrees(lon1_bottom_rad)
    lat1_bottom = np.degrees(lat1_bottom_rad)
    lon2_bottom = np.degrees(lon2_bottom_rad)
    lat2_bottom = np.degrees(lat2_bottom_rad)

    return lon1_bottom, lat1_bottom, lon2_bottom, lat2_bottom


def sph2cart(lon, lat, radius):
    """Convert spherical coordinates to Cartesian"""
    lon_rad = np.deg2rad(lon)
    lat_rad = np.deg2rad(lat)
    x = radius * np.cos(lat_rad) * np.cos(lon_rad)
    y = radius * np.cos(lat_rad) * np.sin(lon_rad)
    z = radius * np.sin(lat_rad)
    return x, y, z


def cart2sph(x, y, z):
    """Convert Cartesian coordinates to spherical"""
    azimuth = np.arctan2(y, x)
    elevation = np.arctan2(z, np.sqrt(x**2 + y**2))
    r = np.sqrt(x**2 + y**2 + z**2)
    return azimuth, elevation, r


# ---------------------------------------------------------
# Main Trame App class
# ---------------------------------------------------------


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

    @staticmethod
    def _shift_longitudes_df(data_df, columns, shift=SHIFT_LON):
        shifted = data_df.copy()
        for column in columns:
            shifted[column] = shifted[column] + shift
        return shifted

    @staticmethod
    def _shift_polygon_df(data_df, polygon_key="polygon", shift=SHIFT_LON):
        shifted = data_df.copy()
        shifted[polygon_key] = [
            [[pt[0] + shift, pt[1]] for pt in polygon]
            for polygon in data_df[polygon_key]
        ]
        return shifted

    @staticmethod
    def _build_fault_proj_data(segment):
        fault_proj_required = {
            "lon1",
            "lat1",
            "lon2",
            "lat2",
            "dip",
            "locking_depth",
        }
        fault_proj_available = fault_proj_required.issubset(segment.columns)
        if not fault_proj_available:
            return False, None

        fault_proj_polygons = []
        fault_proj_dips = []
        fault_proj_names = []
        for i in range(len(segment)):
            dip_deg = segment["dip"].iloc[i]
            locking_depth = segment["locking_depth"].iloc[i]
            if not np.isfinite(dip_deg) or not np.isfinite(locking_depth):
                continue
            if abs(dip_deg - 90.0) <= 1e-6:
                continue

            lon1 = segment["lon1"].iloc[i]
            lat1 = segment["lat1"].iloc[i]
            lon2 = segment["lon2"].iloc[i]
            lat2 = segment["lat2"].iloc[i]

            lon1_bot, lat1_bot, lon2_bot, lat2_bot = calculate_fault_bottom_edge(
                lon1,
                lat1,
                lon2,
                lat2,
                locking_depth,
                dip_deg,
            )
            fault_proj_polygons.append(
                [
                    [lon1, lat1],
                    [lon2, lat2],
                    [lon2_bot, lat2_bot],
                    [lon1_bot, lat1_bot],
                    [lon1, lat1],
                ]
            )
            fault_proj_dips.append(float(dip_deg))
            if "name" in segment.columns:
                fault_proj_names.append(str(segment["name"].iloc[i]))
            else:
                fault_proj_names.append("")

        if not fault_proj_polygons:
            return True, None

        fault_proj_df = pd.DataFrame(
            {
                "polygon": fault_proj_polygons,
                "dip": fault_proj_dips,
                "name": fault_proj_names,
            }
        )
        return True, fault_proj_df

    @staticmethod
    def _build_tde_data(meshes):
        tde_required = {
            "lon1",
            "lat1",
            "dep1",
            "lon2",
            "lat2",
            "dep2",
            "lon3",
            "lat3",
            "dep3",
            "mesh_idx",
            "strike_slip_rate",
            "dip_slip_rate",
        }
        tde_available = tde_required.issubset(meshes.columns)
        if not tde_available:
            return False, None, None

        lon1_mesh = meshes["lon1"].to_numpy().copy()
        lat1_mesh = meshes["lat1"].to_numpy()
        dep1_mesh = meshes["dep1"].to_numpy()
        lon2_mesh = meshes["lon2"].to_numpy().copy()
        lat2_mesh = meshes["lat2"].to_numpy()
        dep2_mesh = meshes["dep2"].to_numpy()
        lon3_mesh = meshes["lon3"].to_numpy().copy()
        lat3_mesh = meshes["lat3"].to_numpy()
        dep3_mesh = meshes["dep3"].to_numpy()
        mesh_idx = meshes["mesh_idx"].to_numpy()

        # Wrap longitude to 0-360
        lon1_mesh[lon1_mesh < 0] += 360
        lon2_mesh[lon2_mesh < 0] += 360
        lon3_mesh[lon3_mesh < 0] += 360

        # Calculate element geometry for steep dipping meshes
        tri_leg1 = np.transpose(
            [
                np.deg2rad(lon2_mesh - lon1_mesh),
                np.deg2rad(lat2_mesh - lat1_mesh),
                (1 + KM2M * dep2_mesh / RADIUS_EARTH)
                - (1 + KM2M * dep1_mesh / RADIUS_EARTH),
            ]
        )
        tri_leg2 = np.transpose(
            [
                np.deg2rad(lon3_mesh - lon1_mesh),
                np.deg2rad(lat3_mesh - lat1_mesh),
                (1 + KM2M * dep3_mesh / RADIUS_EARTH)
                - (1 + KM2M * dep1_mesh / RADIUS_EARTH),
            ]
        )
        norm_vec = np.cross(tri_leg1, tri_leg2)
        tri_area = np.linalg.norm(norm_vec, axis=1)
        azimuth, elevation, r = cart2sph(norm_vec[:, 0], norm_vec[:, 1], norm_vec[:, 2])
        strike = wrap2360(-np.rad2deg(azimuth))
        dip = 90 - np.rad2deg(elevation)
        dip[dip > 90] = 180.0 - dip[dip > 90]

        # Project steeply dipping meshes
        mesh_list = np.unique(mesh_idx)
        proj_mesh_flag = np.zeros_like(mesh_list)
        mesh_area = np.zeros_like(mesh_list, dtype=float)
        for i in mesh_list:
            this_mesh_els = mesh_idx == i
            mesh_area[i] = np.mean(tri_area[this_mesh_els])
            this_mesh_dip = np.mean(dip[this_mesh_els])
            if this_mesh_dip > 75:
                proj_mesh_flag[i] = 1
                dip_dir = np.mean(np.deg2rad(strike[this_mesh_els] + 90))
                lon1_mesh[this_mesh_els] += np.sin(dip_dir) * np.rad2deg(
                    np.abs(KM2M * dep1_mesh[this_mesh_els] / RADIUS_EARTH)
                )
                lat1_mesh[this_mesh_els] += np.cos(dip_dir) * np.rad2deg(
                    np.abs(KM2M * dep1_mesh[this_mesh_els] / RADIUS_EARTH)
                )
                lon2_mesh[this_mesh_els] += np.sin(dip_dir) * np.rad2deg(
                    np.abs(KM2M * dep2_mesh[this_mesh_els] / RADIUS_EARTH)
                )
                lat2_mesh[this_mesh_els] += np.cos(dip_dir) * np.rad2deg(
                    np.abs(KM2M * dep2_mesh[this_mesh_els] / RADIUS_EARTH)
                )
                lon3_mesh[this_mesh_els] += np.sin(dip_dir) * np.rad2deg(
                    np.abs(KM2M * dep3_mesh[this_mesh_els] / RADIUS_EARTH)
                )
                lat3_mesh[this_mesh_els] += np.cos(dip_dir) * np.rad2deg(
                    np.abs(KM2M * dep3_mesh[this_mesh_els] / RADIUS_EARTH)
                )

        proj_mesh_idx = np.where(proj_mesh_flag)[0]

        # Determine mesh perimeter
        edge1_lon = np.array((lon1_mesh, lon2_mesh))
        edge1_lat = np.array((lat1_mesh, lat2_mesh))
        edge1_array = np.vstack(
            (np.sort(edge1_lon, axis=0), np.sort(edge1_lat, axis=0), mesh_idx)
        )
        edge2_lon = np.array((lon2_mesh, lon3_mesh))
        edge2_lat = np.array((lat2_mesh, lat3_mesh))
        edge2_array = np.vstack(
            (np.sort(edge2_lon, axis=0), np.sort(edge2_lat, axis=0), mesh_idx)
        )
        edge3_lon = np.array((lon3_mesh, lon1_mesh))
        edge3_lat = np.array((lat3_mesh, lat1_mesh))
        edge3_array = np.vstack(
            (np.sort(edge3_lon, axis=0), np.sort(edge3_lat, axis=0), mesh_idx)
        )
        all_edge_array = np.concatenate((edge1_array, edge2_array, edge3_array), axis=1)

        edge1_array_unsorted = np.vstack((edge1_lon, edge1_lat, mesh_idx))
        edge2_array_unsorted = np.vstack((edge2_lon, edge2_lat, mesh_idx))
        edge3_array_unsorted = np.vstack((edge3_lon, edge3_lat, mesh_idx))
        all_edge_array_unsorted = np.concatenate(
            (edge1_array_unsorted, edge2_array_unsorted, edge3_array_unsorted), axis=1
        )

        unique_edges, unique_edge_index, edge_count = np.unique(
            all_edge_array, return_index=True, return_counts=True, axis=1
        )
        unique_edges_unsorted = all_edge_array_unsorted[:, unique_edge_index]
        perim_edges = unique_edges_unsorted[:, edge_count == 1]
        proj_mesh_edge_flag = np.isin(perim_edges[-1, :], proj_mesh_idx).astype(int)

        # Sort plotted mesh data, based on total mesh areas
        mesh_plot_order = np.argsort(-mesh_area)
        mesh_plot_order_index = []
        for i in mesh_plot_order:
            mesh_plot_order_index.extend(np.argwhere(mesh_idx == i).flatten().tolist())
        mesh_plot_order_index = np.array(mesh_plot_order_index, dtype=int)

        tde_df = None
        if mesh_plot_order_index.size:
            tde_df = pd.DataFrame(
                {
                    "polygon": [
                        [
                            [lon1_mesh[j], lat1_mesh[j]],
                            [lon2_mesh[j], lat2_mesh[j]],
                            [lon3_mesh[j], lat3_mesh[j]],
                        ]
                        for j in mesh_plot_order_index
                    ],
                    "ss_rate": meshes["strike_slip_rate"].to_numpy()[
                        mesh_plot_order_index
                    ],
                    "ds_rate": meshes["dip_slip_rate"].to_numpy()[
                        mesh_plot_order_index
                    ],
                }
            )

        tde_perim_df = None
        if perim_edges.size:
            tde_perim_df = pd.DataFrame(
                {
                    "start_lon": perim_edges[0, :],
                    "start_lat": perim_edges[2, :],
                    "end_lon": perim_edges[1, :],
                    "end_lat": perim_edges[3, :],
                    "proj_col": proj_mesh_edge_flag,
                }
            )

        return True, tde_df, tde_perim_df

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

    @staticmethod
    def _is_valid_data_folder(folder_path):
        required = {"model_station.csv", "model_segment.csv", "model_meshes.csv"}
        return all((folder_path / name).is_file() for name in required)

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
        if not self._is_valid_data_folder(folder_path):
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

        # Read CSV files
        station = pd.read_csv(folder_name / "model_station.csv")
        segment = pd.read_csv(folder_name / "model_segment.csv")
        meshes = pd.read_csv(folder_name / "model_meshes.csv")

        # Calculate residual magnitude
        resmag = np.sqrt(
            np.power(station.model_east_vel_residual, 2)
            + np.power(station.model_north_vel_residual, 2)
        )

        # Convert station coordinates to Web Mercator
        lon_station = station.lon.to_numpy()
        lat_station = station.lat.to_numpy()
        x_station, y_station = wgs84_to_web_mercator(lon_station, lat_station)

        # Convert segment coordinates to Web Mercator
        lon1_seg = segment.lon1.to_numpy()
        lat1_seg = segment.lat1.to_numpy()
        lon2_seg = segment.lon2.to_numpy()
        lat2_seg = segment.lat2.to_numpy()
        x1_seg, y1_seg = wgs84_to_web_mercator(lon1_seg, lat1_seg)
        x2_seg, y2_seg = wgs84_to_web_mercator(lon2_seg, lat2_seg)

        fault_proj_available, fault_proj_df = self._build_fault_proj_data(segment)
        tde_available, tde_df, tde_perim_df = self._build_tde_data(meshes)

        # Store data
        data = {
            "station": station,
            "segment": segment,
            "meshes": meshes,
            "resmag": resmag,
            "x_station": x_station,
            "y_station": y_station,
            "x1_seg": x1_seg,
            "y1_seg": y1_seg,
            "x2_seg": x2_seg,
            "y2_seg": y2_seg,
            "tde_available": tde_available,
            "tde_df": tde_df,
            "tde_perim_df": tde_perim_df,
            "fault_proj_available": fault_proj_available,
            "fault_proj_df": fault_proj_df,
        }

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
        layers = []

        # Process folder 1 data
        if self.folder_1_data is not None:
            layers.extend(self._create_layers_for_folder(1, self.folder_1_data))

        # Process folder 2 data
        if self.folder_2_data is not None:
            layers.extend(self._create_layers_for_folder(2, self.folder_2_data))

        self.ctrl.deck_update(self._build_deck(layers))

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

    def _create_layers_for_folder(self, folder_number, data):
        """Create DeckGL layers for a specific folder's data"""
        layers = []
        vector_layers = []
        station = data["station"]
        x_station = data["x_station"]
        y_station = data["y_station"]

        # Get visibility state
        vis_keys = (
            "show_locs",
            "show_obs",
            "show_mod",
            "show_res",
            "show_rot",
            "show_seg",
            "show_tri",
            "show_str",
            "show_mog",
        )
        vis = {k: self.state[f"{k}_{folder_number}"] for k in vis_keys}

        colors = TYPE_COLORS[folder_number]
        base_width = LINE_WIDTHS[folder_number]

        def add_velocity_layer(
            layer_id_prefix, east_component, north_component, base_color, line_width
        ):
            """Add base and -360 shifted velocity line layers using the same color."""
            velocity_scale = self.state.velocity_scale * VELOCITY_SCALE
            x_end = x_station + velocity_scale * east_component
            y_end = y_station + velocity_scale * north_component
            end_lon, end_lat = web_mercator_to_wgs84(x_end, y_end)
            end_lon = normalize_longitude_difference(station.lon.values, end_lon)

            base_df = pd.DataFrame(
                {
                    "start_lon": station.lon.to_numpy(),
                    "start_lat": station.lat.to_numpy(),
                    "end_lon": end_lon,
                    "end_lat": end_lat,
                }
            )

            add_line_layer(
                layer_id_prefix,
                base_df,
                base_color,
                line_width,
                width_min_pixels=1,
                pickable=False,
                layer_list=vector_layers,
            )

        def add_line_layer(
            layer_id_prefix,
            data_df,
            get_color,
            line_width,
            width_min_pixels=1,
            pickable=False,
            layer_list=None,
        ):
            """Add base and -360 shifted line layers."""
            target_layers = layer_list if layer_list is not None else layers
            target_layers.append(
                pdk.Layer(
                    "LineLayer",
                    data=data_df,
                    get_source_position=["start_lon", "start_lat"],
                    get_target_position=["end_lon", "end_lat"],
                    get_color=get_color,
                    get_width=line_width,
                    width_min_pixels=width_min_pixels,
                    pickable=pickable,
                    id=f"{layer_id_prefix}_{folder_number}",
                )
            )

            shift_df = self._shift_longitudes_df(data_df, ["start_lon", "end_lon"])
            target_layers.append(
                pdk.Layer(
                    "LineLayer",
                    data=shift_df,
                    get_source_position=["start_lon", "start_lat"],
                    get_target_position=["end_lon", "end_lat"],
                    get_color=get_color,
                    get_width=line_width,
                    width_min_pixels=width_min_pixels,
                    pickable=pickable,
                    id=f"{layer_id_prefix}_shift_{folder_number}",
                )
            )

        def add_polygon_layer(
            layer_id_prefix,
            data_df,
            fill_color,
            line_color,
            line_width,
            line_width_min_pixels=1,
            stroked=True,
            pickable=True,
        ):
            """Add base and -360 shifted polygon layers."""
            layers.append(
                pdk.Layer(
                    "PolygonLayer",
                    data=data_df,
                    get_polygon="polygon",
                    get_fill_color=fill_color,
                    get_line_color=line_color,
                    get_line_width=line_width,
                    filled=True,
                    stroked=stroked,
                    line_width_min_pixels=line_width_min_pixels,
                    pickable=pickable,
                    id=f"{layer_id_prefix}_{folder_number}",
                )
            )

            shift_df = self._shift_polygon_df(data_df)
            layers.append(
                pdk.Layer(
                    "PolygonLayer",
                    data=shift_df,
                    get_polygon="polygon",
                    get_fill_color=fill_color,
                    get_line_color=line_color,
                    get_line_width=line_width,
                    filled=True,
                    stroked=stroked,
                    line_width_min_pixels=line_width_min_pixels,
                    pickable=pickable,
                    id=f"{layer_id_prefix}_shift_{folder_number}",
                )
            )

        def map_slip_colors(values):
            """Map slip values to discrete RdBu[11] colors."""
            colors_array = []
            span = SLIP_RATE_MAX - SLIP_RATE_MIN
            for raw_value in values:
                value = raw_value
                if not np.isfinite(value):
                    value = 0.0
                value = float(np.clip(value, SLIP_RATE_MIN, SLIP_RATE_MAX))
                position = (value - SLIP_RATE_MIN) / span
                index = int(np.floor(position * len(RDBU_11)))
                index = max(0, min(len(RDBU_11) - 1, index))
                r, g, b = RDBU_11[index]
                colors_array.append([r, g, b, 255])
            return colors_array

        def add_scatter_layer(
            layer_id_prefix,
            data_df,
            fill_color,
            radius,
            radius_min_pixels=1,
            radius_max_pixels=10,
            pickable=False,
        ):
            layers.append(
                pdk.Layer(
                    "ScatterplotLayer",
                    data=data_df,
                    get_position=["lon", "lat"],
                    get_fill_color=fill_color,
                    get_radius=radius,
                    radius_min_pixels=radius_min_pixels,
                    radius_max_pixels=radius_max_pixels,
                    pickable=pickable,
                    id=f"{layer_id_prefix}_{folder_number}",
                )
            )
            shift_df = self._shift_longitudes_df(data_df, ["lon"])
            layers.append(
                pdk.Layer(
                    "ScatterplotLayer",
                    data=shift_df,
                    get_position=["lon", "lat"],
                    get_fill_color=fill_color,
                    get_radius=radius,
                    radius_min_pixels=radius_min_pixels,
                    radius_max_pixels=radius_max_pixels,
                    pickable=pickable,
                    id=f"{layer_id_prefix}_shift_{folder_number}",
                )
            )

        def format_number(value, precision=4):
            try:
                if not np.isfinite(value):
                    return "n/a"
            except TypeError:
                return "n/a"
            return f"{value:.{precision}f}"

        def format_segment_tooltip(
            name, lon1, lat1, lon2, lat2, ss_rate, ds_rate, ts_rate
        ):
            return (
                f"<b>Name</b>: {name}<br/>"
                f"<b>Start</b>: ({format_number(lon1)}, {format_number(lat1)})<br/>"
                f"<b>End</b>: ({format_number(lon2)}, {format_number(lat2)})<br/>"
                f"<b>Strike-Slip Rate</b>: {format_number(ss_rate)}<br/>"
                f"<b>Dip-Slip Rate</b>: {format_number(ds_rate)}<br/>"
                f"<b>Tensile-Slip Rate</b>: {format_number(ts_rate)}"
            )

        # Station locations (only when explicitly requested)
        if self.state[f"show_locs_{folder_number}"]:
            station_df = pd.DataFrame(
                {
                    "lon": station.lon.to_numpy(),
                    "lat": station.lat.to_numpy(),
                    "name": station.name.to_numpy(),
                }
            )
            station_df["tooltip"] = [
                f"<b>Name</b>: {name}" for name in station_df["name"]
            ]

            add_scatter_layer(
                "stations",
                station_df,
                colors["loc"],
                3000,
                radius_min_pixels=2,
                radius_max_pixels=5,
                pickable=True,
            )

        # Observed velocities
        if vis["show_obs"]:
            # Velocity data is in mm/yr, VELOCITY_SCALE converts to m/yr; Web Mercator uses meters
            add_velocity_layer(
                "obs_vel",
                station.east_vel.values,
                station.north_vel.values,
                colors["obs"],
                base_width,
            )

        # Modeled velocities
        if vis["show_mod"]:
            add_velocity_layer(
                "mod_vel",
                station.model_east_vel.values,
                station.model_north_vel.values,
                colors["mod"],
                base_width,
            )

        # Residual velocities
        if vis["show_res"]:
            add_velocity_layer(
                "res_vel",
                station.model_east_vel_residual.values,
                station.model_north_vel_residual.values,
                colors["res"],
                base_width,
            )

        # Rotation velocities
        if vis["show_rot"]:
            add_velocity_layer(
                "rot_vel",
                station.model_east_vel_rotation.values,
                station.model_north_vel_rotation.values,
                colors["rot"],
                base_width,
            )

        # Segment elastic velocities
        if vis["show_seg"]:
            add_velocity_layer(
                "seg_vel",
                station.model_east_elastic_segment.values,
                station.model_north_elastic_segment.values,
                colors["seg"],
                base_width,
            )

        # TDE velocities
        if vis["show_tri"]:
            add_velocity_layer(
                "tde_vel",
                station.model_east_vel_tde.values,
                station.model_north_vel_tde.values,
                colors["tde"],
                base_width,
            )

        # Strain rate velocities
        if vis["show_str"]:
            add_velocity_layer(
                "str_vel",
                station.model_east_vel_block_strain_rate.values,
                station.model_north_vel_block_strain_rate.values,
                colors["str"],
                base_width,
            )

        # Mogi velocities
        if vis["show_mog"]:
            add_velocity_layer(
                "mog_vel",
                station.model_east_vel_mogi.values,
                station.model_north_vel_mogi.values,
                colors["mog"],
                base_width,
            )

        # TDE slip rates (triangular dislocation elements)
        show_tde = self.state[f"show_tde_{folder_number}"]
        if show_tde:
            if not data.get("tde_available", False):
                self.state[f"show_tde_{folder_number}"] = False
            else:
                tde_df = data.get("tde_df")
                if tde_df is not None and not tde_df.empty:
                    tde_slip_type = self.state[f"tde_slip_type_{folder_number}"]
                    if tde_slip_type == "ss":
                        slip_values = tde_df["ss_rate"].to_numpy()
                    else:
                        slip_values = tde_df["ds_rate"].to_numpy()
                    tde_df = tde_df.copy()
                    tde_df["color"] = map_slip_colors(slip_values)
                    add_polygon_layer(
                        "tde",
                        tde_df,
                        "color",
                        [0, 0, 0, 0],
                        0,
                        line_width_min_pixels=0,
                        stroked=False,
                        pickable=False,
                    )

                tde_perim_df = data.get("tde_perim_df")
                if tde_perim_df is not None and not tde_perim_df.empty:
                    tde_perim_df = tde_perim_df.copy()
                    tde_perim_df["color"] = [
                        [255, 0, 0, 255] if int(flag) == 1 else [0, 0, 0, 255]
                        for flag in tde_perim_df["proj_col"]
                    ]
                    add_line_layer(
                        "tde_perim",
                        tde_perim_df,
                        "color",
                        1,
                        width_min_pixels=1,
                        pickable=False,
                    )

        seg_tooltip_enabled = folder_number == 1

        # Base fault segments (always visible once data is loaded)
        segment = data["segment"]
        fault_lines_df = pd.DataFrame(
            {
                "start_lon": segment.lon1.to_numpy(),
                "start_lat": segment.lat1.to_numpy(),
                "end_lon": segment.lon2.to_numpy(),
                "end_lat": segment.lat2.to_numpy(),
            }
        )
        if seg_tooltip_enabled:
            if {
                "model_strike_slip_rate",
                "model_dip_slip_rate",
                "model_tensile_slip_rate",
            }.issubset(segment.columns):
                ss_rates = segment.model_strike_slip_rate.to_numpy()
                ds_rates = (
                    segment.model_dip_slip_rate.to_numpy()
                    - segment.model_tensile_slip_rate.to_numpy()
                )
                ts_rates = segment.model_tensile_slip_rate.to_numpy()
            else:
                ss_rates = np.full(len(segment), np.nan)
                ds_rates = np.full(len(segment), np.nan)
                ts_rates = np.full(len(segment), np.nan)
            fault_lines_df["tooltip"] = [
                format_segment_tooltip(
                    name,
                    lon1,
                    lat1,
                    lon2,
                    lat2,
                    ss,
                    ds,
                    ts,
                )
                for name, lon1, lat1, lon2, lat2, ss, ds, ts in zip(
                    segment.name.to_numpy(),
                    segment.lon1.to_numpy(),
                    segment.lat1.to_numpy(),
                    segment.lon2.to_numpy(),
                    segment.lat2.to_numpy(),
                    ss_rates,
                    ds_rates,
                    ts_rates,
                )
            ]
        base_style = FAULT_LINE_STYLE[folder_number]
        add_line_layer(
            "fault_lines",
            fault_lines_df,
            base_style["color"],
            base_style["width"],
            width_min_pixels=1,
            pickable=seg_tooltip_enabled,
        )

        # Fault segments
        show_seg_color = self.state[f"show_seg_color_{folder_number}"]
        if show_seg_color:
            segment = data["segment"]
            seg_slip_type = self.state[f"seg_slip_type_{folder_number}"]

            required_cols = {
                "model_strike_slip_rate",
                "model_dip_slip_rate",
                "model_tensile_slip_rate",
            }
            if not required_cols.issubset(segment.columns):
                if self.state[f"show_seg_color_{folder_number}"]:
                    self.state[f"show_seg_color_{folder_number}"] = False
                return layers

            # Get slip values based on type (strike-slip or dip-slip)
            if seg_slip_type == "ss":
                slip_values = segment.model_strike_slip_rate.to_numpy()
            else:  # ds
                slip_values = (
                    segment.model_dip_slip_rate.to_numpy()
                    - segment.model_tensile_slip_rate.to_numpy()
                )

            # Create segment lines with color based on slip rate
            seg_lines_df = pd.DataFrame(
                {
                    "start_lon": segment.lon1.to_numpy(),
                    "start_lat": segment.lat1.to_numpy(),
                    "end_lon": segment.lon2.to_numpy(),
                    "end_lat": segment.lat2.to_numpy(),
                    "slip_rate": slip_values,
                }
            )

            colors_array = map_slip_colors(slip_values)
            seg_lines_df["color"] = colors_array
            if seg_tooltip_enabled and "tooltip" in fault_lines_df.columns:
                seg_lines_df["tooltip"] = fault_lines_df["tooltip"].to_numpy()

            add_line_layer(
                "segments",
                seg_lines_df,
                "color",
                3,
                width_min_pixels=2,
                pickable=seg_tooltip_enabled,
            )

        # Fault surface projections
        show_fault_proj = self.state[f"show_fault_proj_{folder_number}"]
        if show_fault_proj:
            if not data.get("fault_proj_available", False):
                self.state[f"show_fault_proj_{folder_number}"] = False
            else:
                fault_proj_df = data.get("fault_proj_df")
                if fault_proj_df is not None and not fault_proj_df.empty:
                    style = FAULT_PROJ_STYLE[folder_number]
                    add_polygon_layer(
                        "fault_proj",
                        fault_proj_df,
                        style["fill"],
                        style["line"],
                        1,
                        pickable=False,
                    )

        layers.extend(vector_layers)
        return layers

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
        self._set_velocity_scale(self.state.velocity_scale / 10.0)

    @controller.set("velocity_scale_mag_up")
    def velocity_scale_mag_up(self):
        self._set_velocity_scale(self.state.velocity_scale * 10.0)

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
                                        "/10",
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
                                        "x10",
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
