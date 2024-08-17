import geopandas as gpd
from os import path, makedirs
from glob import glob
import numpy as np
from typing import Union
from shapely.geometry import Point, Polygon, LineString
from enum import Enum
from pyproj import CRS
from artof_utils.helpers import array
from artof_utils.helpers import shape as shp
from artof_utils.schemas.settings import load_settings


class GeomType(str, Enum):
    POINT = 'Point'
    MULTIPOINT = 'MultiPoint'
    LINESTRING = 'LineString'
    POLYGON = 'Polygon'


class Shapefile:
    def __init__(self, folder_path):
        self.empty = True
        self.geom_type = None
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
            self.geom_type = self.gdf.geom_type.iloc[0] if len(self.gdf.geom_type) else None
            self.empty = (len(self.gdf.geometry) == 1 and
                          self.geom_type == GeomType.POINT and
                          list(self.gdf.geometry[0].coords) == [(0.0, 0.0)]) or self.geom_type is None

    @property
    def context(self):
        r = dict()

        r['empty'] = self.empty
        r['hasZ'] = bool(self.gdf.has_z.iloc[0]) if len(self.gdf.has_z) else False
        r['wkid'] = self.gdf.crs.to_epsg()

        wgs84_crs = 'EPSG:4326'  # WGS 84
        input_crs = 'EPSG:%d' % r['wkid']

        if self.geom_type == GeomType.POINT:
            if r['hasZ']:
                r['points'] = self.gdf.geometry.apply(lambda point: [point.x, point.y, point.z]).to_list()
            else:
                r['points'] = self.gdf.geometry.apply(lambda point: [point.x, point.y]).to_list()
            r['latlng'] = shp.transform_crs(input_crs, wgs84_crs, r['points'])
        elif self.geom_type == GeomType.MULTIPOINT:
            if r['hasZ']:
                np_points = np.array(self.gdf.geometry.apply(
                    lambda multipoint: [[point.x, point.y, point.z] for point in multipoint.geoms]).to_list())
                np_points = np_points.squeeze(axis=1)
            else:
                np_points = np.array(self.gdf.geometry.apply(
                    lambda multipoint: [[point.x, point.y] for point in multipoint.geoms]).to_list())
                np_points = np_points.squeeze(axis=1)
            r['points'] = [list(point) for point in np_points]
            r['latlng'] = shp.transform_crs(input_crs, wgs84_crs, r['points'])
        elif self.geom_type == GeomType.LINESTRING:
            if r['hasZ']:
                r['paths'] = self.gdf.geometry.apply(
                    lambda linestring: [[x, y, z] for x, y, z in linestring.coords]).to_list()
            else:
                r['paths'] = self.gdf.geometry.apply(
                    lambda linestring: [[x, y] for x, y in linestring.coords]).to_list()
            r['latlng'] = [shp.transform_crs(input_crs, wgs84_crs, path_) for path_ in r['paths']]
        elif self.geom_type == GeomType.POLYGON:
            if r['hasZ']:
                r['rings'] = self.gdf.geometry.apply(
                    lambda polygon: [[x, y, z] for x, y, z in polygon.exterior.coords]).to_list()
            else:
                r['rings'] = self.gdf.geometry.apply(
                    lambda polygon: [[x, y] for x, y in polygon.exterior.coords]).to_list()
            r['latlng'] = [shp.transform_crs(input_crs, wgs84_crs, ring_) for ring_ in r['rings']]
        else:
            r['latlng'] = []

        return r

    def update(self, geometries: Union[list, np.array, gpd.GeoDataFrame], geom_type: GeomType = None, epsg: int = 0):
        if isinstance(geometries, gpd.GeoDataFrame):
            # Process gdf as geometry
            assert geometries.crs, 'No crs in shapefile'
            if geom_type:
                assert geometries.geom_type[0] == geom_type, 'Only %s geometries are supported' % geom_type

            self.gdf = geometries
            self.save()
        else:
            # Process list and unions as geometry
            assert self.gdf.crs, 'No crs in shapefile'

            if epsg:
                # Convert to this crc
                input_crs = 'EPSG:%d' % epsg
                gdf_crs = 'EPSG:%d' % self.gdf.crs.to_epsg()
                if input_crs != gdf_crs:
                    geometries = shp.transform_crs(input_crs, gdf_crs, geometries)

            depth = array.get_depth(geometries)

            if not geom_type:
                # Use geometry type of first geometry
                assert len(self.gdf) > 0 and self.geom_type is not None, 'No data in shapefile'
                geom_type = self.geom_type
            else:
                self.geom_type = geom_type

            new_geom = None
            if geom_type == GeomType.POINT or geom_type == GeomType.MULTIPOINT:
                new_geom = [Point(geom[0], geom[1]) for geom in np.array(geometries).squeeze()]
            elif geom_type == GeomType.LINESTRING:
                if depth == 2:
                    geometries = np.expand_dims(geometries, axis=0) if isinstance(geometries, np.ndarray) else [
                        geometries]
                # Create array of rings when only one ring is provided
                new_geom = [LineString(geom) for geom in geometries]
            elif geom_type == GeomType.POLYGON:
                # Create array of rings when only one ring is provided
                if depth == 2:
                    geometries = (np.expand_dims(geometries, axis=0) if isinstance(geometries, np.ndarray) else
                                  [[np.array(geom) for geom in geometries]])
                elif depth == 3:
                    if isinstance(geometries, list):
                        geometries = [np.array(geom) for geom in geometries]
                elif depth == 4:
                    geometries = geometries[0]
                else:
                    raise ValueError('unsupported depth of array')

                # Check if rings are closed and if not close them
                for geom in geometries:
                    assert len(geom) >= 3, 'Empty polygon'
                    if np.allclose(geom[0], geom[-1]):
                        geom = np.vstack((geom, geom[0]))  # update the geometry
                new_geom = [Polygon(geom) for geom in geometries]

            if new_geom:
                self.gdf = gpd.GeoDataFrame(geometry=new_geom, crs=self.gdf.crs)
                self.save()

        self.empty = False

    def save(self, other_folder_path=None):
        if other_folder_path:
            makedirs(other_folder_path, exist_ok=True)
            save_file_path = path.join(other_folder_path, path.basename(self.file_path))
        else:
            save_file_path = self.file_path

        self.gdf.to_file(save_file_path)

    def get_geom_type(self):
        if len(self.gdf) == 0:
            return None

        return self.gdf.geom_type[0]
