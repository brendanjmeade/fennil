from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from fennil.app.geo_projs import (
    DIP_EPS,
    KM2M,
    RADIUS_EARTH,
    VERTICAL_DIP_DEG,
    calculate_fault_bottom_edge,
    cart2sph,
    wgs84_to_web_mercator,
    wrap2360,
)

PROJ_MESH_DIP_THRESHOLD_DEG = 75.0


@dataclass
class Dataset:
    station: pd.DataFrame
    segment: pd.DataFrame
    meshes: pd.DataFrame
    resmag: np.ndarray
    x_station: np.ndarray
    y_station: np.ndarray
    x1_seg: np.ndarray
    y1_seg: np.ndarray
    x2_seg: np.ndarray
    y2_seg: np.ndarray
    tde_available: bool
    tde_df: pd.DataFrame | None
    tde_perim_df: pd.DataFrame | None
    fault_proj_available: bool
    fault_proj_df: pd.DataFrame | None


def is_valid_data_folder(folder_path):
    required = {"model_station.csv", "model_segment.csv", "model_meshes.csv"}
    return all((folder_path / name).is_file() for name in required)


def build_fault_proj_data(segment):
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
        if abs(dip_deg - VERTICAL_DIP_DEG) <= DIP_EPS:
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


def build_tde_data(meshes):
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

    lon1_mesh[lon1_mesh < 0] += 360
    lon2_mesh[lon2_mesh < 0] += 360
    lon3_mesh[lon3_mesh < 0] += 360

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

    mesh_list = np.unique(mesh_idx)
    proj_mesh_flag = np.zeros_like(mesh_list)
    mesh_area = np.zeros_like(mesh_list, dtype=float)
    for i in mesh_list:
        this_mesh_els = mesh_idx == i
        mesh_area[i] = np.mean(tri_area[this_mesh_els])
        this_mesh_dip = np.mean(dip[this_mesh_els])
        if this_mesh_dip > PROJ_MESH_DIP_THRESHOLD_DEG:
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
                "ss_rate": meshes["strike_slip_rate"].to_numpy()[mesh_plot_order_index],
                "ds_rate": meshes["dip_slip_rate"].to_numpy()[mesh_plot_order_index],
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


def load_folder_data(folder_path):
    folder_path = Path(folder_path)

    station = pd.read_csv(folder_path / "model_station.csv")
    segment = pd.read_csv(folder_path / "model_segment.csv")
    meshes = pd.read_csv(folder_path / "model_meshes.csv")

    resmag = np.sqrt(
        np.power(station.model_east_vel_residual, 2)
        + np.power(station.model_north_vel_residual, 2)
    )

    lon_station = station.lon.to_numpy()
    lat_station = station.lat.to_numpy()
    x_station, y_station = wgs84_to_web_mercator(lon_station, lat_station)

    lon1_seg = segment.lon1.to_numpy()
    lat1_seg = segment.lat1.to_numpy()
    lon2_seg = segment.lon2.to_numpy()
    lat2_seg = segment.lat2.to_numpy()
    x1_seg, y1_seg = wgs84_to_web_mercator(lon1_seg, lat1_seg)
    x2_seg, y2_seg = wgs84_to_web_mercator(lon2_seg, lat2_seg)

    fault_proj_available, fault_proj_df = build_fault_proj_data(segment)
    tde_available, tde_df, tde_perim_df = build_tde_data(meshes)

    return Dataset(
        station=station,
        segment=segment,
        meshes=meshes,
        resmag=resmag,
        x_station=x_station,
        y_station=y_station,
        x1_seg=x1_seg,
        y1_seg=y1_seg,
        x2_seg=x2_seg,
        y2_seg=y2_seg,
        tde_available=tde_available,
        tde_df=tde_df,
        tde_perim_df=tde_perim_df,
        fault_proj_available=fault_proj_available,
        fault_proj_df=fault_proj_df,
    )
