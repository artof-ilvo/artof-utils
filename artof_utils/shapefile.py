import geopandas as gpd
from os import path, makedirs
from glob import glob
from shapely.geometry import Point, Polygon, LineString
from pyproj import CRS
from artof_utils.schemas.settings import load_settings
import json


class Shapefile:
    def __init__(self, folder_path):
        self.gdf_mods = []
        self.gdf = None
        self.props = None
        shape_files = glob(path.join(folder_path, '*.shp'))
        if len(shape_files) == 0:
            # Create a new empty shapefile as it does not exist
            self.file_path = path.join(folder_path, '%s.shp' % path.basename(folder_path))
            settings = load_settings()
            self.gdf = gpd.GeoDataFrame(geometry=[Point(0, 0)], crs=CRS('EPSG:326%d' % settings.gps.utm_zone))
            makedirs(folder_path, exist_ok=True)
            self.save()
        else:
            # Read the shapefile as it exists
            self.file_path = shape_files[0]
            self.gdf = gpd.read_file(self.file_path)

    def get_props(self):
        pass

    @property
    def context(self):
        wgs84_crs = 'EPSG:4326'  # WGS 84
        gdf_wgs84 = self.gdf.to_crs(wgs84_crs)
        return json.loads(gdf_wgs84.to_json())

    def save(self, other_folder_path=None):
        if other_folder_path:
            makedirs(other_folder_path, exist_ok=True)
            save_file_path = path.join(other_folder_path, path.basename(self.file_path))
        else:
            save_file_path = self.file_path

        self.gdf.to_file(save_file_path)

    @property
    def geom_type(self):
        if len(self.gdf) == 0:
            return None

        return self.gdf.geom_type[0]

    def update(self, gdf=None, epsg=None):
        if epsg is not None:
            self.gdf = self.gdf.to_crs(epsg) if gdf is None else gdf.to_crs(epsg)
        else:
            self.gdf = self.gdf if gdf is None else gdf

    def commit(self):
        self.save()
        self.gdf_mods = []

    def commit_last_mod(self):
        self.gdf = self.get_last_mod()
        self.commit()

    def discard(self):
        self.gdf_mods = []

    def get_last_mod(self):
        return self.gdf_mods[-1]