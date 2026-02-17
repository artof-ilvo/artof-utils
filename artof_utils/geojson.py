from typing import Union, Any, Optional
import numpy as np
import pandas as pd
import geopandas as gpd
import os
import json
from os import path, makedirs
from enum import Enum
from shapely.geometry import shape, Point, Polygon, LineString
from artof_utils.helpers import array

class GeomType(str, Enum):
    POINT = 'Point'
    MULTIPOINT = 'MultiPoint'
    LINESTRING = 'LineString'
    POLYGON = 'Polygon'

class GeoJson:
    def __init__(self, folder_path: str, filename: str = "data"):
        self.folder_path = folder_path
        self.filename = filename
        self.file_path = path.join(folder_path, f"{filename}.geojson")
        self.raster_path = os.path.join(self.folder_path, "rasters")
        self.gdf = None
        self.load()

    def load(self):
        """loads the file if it exists or else a empty GeoDataFrame."""
        if path.exists(self.file_path):
            try:
                self.gdf = gpd.read_file(self.file_path)
            except Exception as e:
                print(f"Fout bij laden van {self.file_path}: {e}")
                self.gdf = gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
        else:
            self.gdf = gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")

    def update(self, geometries: Union[list, np.ndarray, gpd.GeoDataFrame, None, dict], 
               name: str, 
               type: Any = "vector", 
               properties: Optional[dict] = None, 
               epsg: int = 0):
        
        if isinstance(geometries, gpd.GeoDataFrame):
            new_gdf = geometries
        else:
            geoms = []

            if isinstance(geometries, dict):
                geoms = [shape(geometries)]
            elif isinstance(geometries, (list, np.ndarray)):
                
                raw_list = geometries.tolist() if isinstance(geometries, np.ndarray) else geometries
                
                if not raw_list:
                    geoms = [None]
                elif hasattr(raw_list[0], 'geom_type'):
                    geoms = raw_list
                else:
                    depth = array.get_depth(geometries)

                    if depth == 1:
                        geoms = [Point(raw_list)]
                    elif depth == 2:
                        if len(raw_list) == 1:
                            geoms = [Point(raw_list[0])]
                        else:
                            geoms = [LineString(raw_list)]
                    elif depth >= 3:
                        if depth == 3:
                            rings = raw_list
                        elif depth == 4:
                            rings = raw_list[0]
                        else:
                            rings = []

                        for ring in rings:
                            ring_arr = np.array(ring)
                            if len(ring_arr) >= 3: 
                                if not np.allclose(ring_arr[0], ring_arr[-1]):
                                    ring_arr = np.vstack((ring_arr, ring_arr[0]))
                                geoms.append(Polygon(ring_arr))
                            elif len(ring_arr) == 2:
                                geoms.append(LineString(ring_arr))
                            elif len(ring_arr) == 1:
                                geoms.append(Point(ring_arr[0]))
            
            elif hasattr(geometries, 'geom_type'):
                geoms = [geometries]
            else:
                geoms = [None]

            input_crs = f"EPSG:{epsg}" if epsg else "EPSG:4326"
            new_gdf = gpd.GeoDataFrame(
                {'name': [name] * len(geoms), 'type': [str(type)] * len(geoms)}, 
                geometry=geoms, 
                crs=input_crs
            )

        if properties: # metadata for tasks
            for key, value in properties.items():
                new_gdf[key] = value

        if new_gdf.crs and new_gdf.crs.to_epsg() != 4326:
            new_gdf = new_gdf.to_crs(epsg=4326)

        if self.gdf is not None and not self.gdf.empty:
            for col in new_gdf.columns:
                if col not in self.gdf.columns:
                    self.gdf[col] = None
                    
            for col in self.gdf.columns:
                if col not in new_gdf.columns:
                    new_gdf[col] = None

            self.gdf = self.gdf[self.gdf['name'] != name]
            self.gdf = pd.concat([self.gdf, new_gdf], ignore_index=True)
        else:
            self.gdf = new_gdf

        self.save()

    def save(self):
        if self.gdf is not None:
            if not path.exists(self.folder_path):
                makedirs(self.folder_path, exist_ok=True)
            
            raster_path = path.join(self.folder_path, "rasters")
            makedirs(raster_path, exist_ok=True)
                
            self.gdf.to_file(self.file_path, driver='GeoJSON')

    def delete(self, name: str):
        """
        Verwijdert een onderdeel uit de GDF en schoont bijbehorende bestanden op.
        """
        if self.gdf is None or self.gdf.empty:
            return

        item_to_delete = self.gdf[self.gdf['name'] == name]
        if item_to_delete.empty:
            print(f"Item '{name}' niet gevonden in GeoJSON.")
            return

        potential_raster = path.join(self.raster_path, f"{name}.tif")
        if path.exists(potential_raster):
            try:
                os.remove(potential_raster)
            except Exception as e:
                print(f"Kon raster voor {name} niet verwijderen: {e}")

        self.gdf = self.gdf[self.gdf['name'] != name]

        self.save()

    @property
    def context(self) -> dict:
        """Geeft de volledige feature collection voor de webapp."""
        if self.gdf is None or self.gdf.empty:
            return {"type": "FeatureCollection", "features": []}
        return json.loads(self.gdf.to_json())

    def get_layer_context(self, layer_name: str) -> dict:
        """Handig om specifiek de geofence of het traject eruit te vissen voor de webapp."""
        if self.gdf is not None and not self.gdf.empty:
            subset = self.gdf[self.gdf['name'] == layer_name]
            if not subset.empty:
                return json.loads(subset.to_json())
        return {}
    
    @property
    def geometry(self):
        """Geeft de shapely geometrie terug voor interne berekeningen."""
        if self.gdf is not None and not self.gdf.empty:
            return self.gdf.geometry.iloc[0] if len(self.gdf) == 1 else self.gdf.geometry.tolist()
        return None