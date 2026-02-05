import numpy as np

SHIFT_LON = -360.0
KM2M = 1.0e3
RADIUS_EARTH = 6371000


def wgs84_to_web_mercator(lon, lat):
    """Converts decimal (longitude, latitude) to Web Mercator (x, y)."""
    earth_radius = 6378137.0
    x = earth_radius * np.deg2rad(lon)
    y = earth_radius * np.log(np.tan(np.pi / 4.0 + np.deg2rad(lat) / 2.0))
    return x, y


def web_mercator_to_wgs84(x, y):
    """Converts Web Mercator (x, y) to WGS84 (longitude, latitude)."""
    earth_radius = 6378137.0
    lon = np.rad2deg(x / earth_radius)
    lat = np.rad2deg(2.0 * np.arctan(np.exp(y / earth_radius)) - np.pi / 2.0)
    return lon, lat


def normalize_longitude_difference(start_lon, end_lon):
    """
    Normalize end longitude to be in the same 360-degree range as start longitude.
    This prevents vectors from wrapping around the world when crossing the date line.
    """
    diff = end_lon - start_lon
    diff = np.where(diff > 180, diff - 360, diff)
    diff = np.where(diff < -180, diff + 360, diff)
    return start_lon + diff


def wrap2360(lon):
    """Wrap longitude to 0-360 range."""
    lon[np.where(lon < 0.0)] += 360.0
    return lon


def calculate_fault_bottom_edge(lon1, lat1, lon2, lat2, depth_km, dip_degrees):
    """Calculate bottom edge coordinates for a dipping fault plane."""
    dip_rad = np.radians(dip_degrees)
    lat1_rad = np.radians(lat1)
    lat2_rad = np.radians(lat2)
    lon1_rad = np.radians(lon1)
    lon2_rad = np.radians(lon2)

    earth_radius_km = 6371.0

    if np.abs(dip_degrees - 90.0) < 1e-6:
        return lon1, lat1, lon2, lat2

    delta_lon = lon2_rad - lon1_rad
    y = np.sin(delta_lon) * np.cos(lat2_rad)
    x = np.cos(lat1_rad) * np.sin(lat2_rad) - np.sin(lat1_rad) * np.cos(
        lat2_rad
    ) * np.cos(delta_lon)
    strike_bearing = np.arctan2(y, x)

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
    """Convert spherical coordinates to Cartesian."""
    lon_rad = np.deg2rad(lon)
    lat_rad = np.deg2rad(lat)
    x = radius * np.cos(lat_rad) * np.cos(lon_rad)
    y = radius * np.cos(lat_rad) * np.sin(lon_rad)
    z = radius * np.sin(lat_rad)
    return x, y, z


def cart2sph(x, y, z):
    """Convert Cartesian coordinates to spherical."""
    lon = np.arctan2(y, x)
    hyp = np.sqrt(x**2 + y**2)
    lat = np.arctan2(z, hyp)
    r = np.sqrt(x**2 + y**2 + z**2)
    return lon, lat, r


def shift_longitudes_df(data_df, columns, shift=SHIFT_LON):
    shifted = data_df.copy()
    for column in columns:
        shifted[column] = shifted[column] + shift
    return shifted


def shift_polygon_df(data_df, polygon_key="polygon", shift=SHIFT_LON):
    shifted = data_df.copy()
    shifted[polygon_key] = [
        [[pt[0] + shift, pt[1]] for pt in polygon] for polygon in data_df[polygon_key]
    ]
    return shifted
