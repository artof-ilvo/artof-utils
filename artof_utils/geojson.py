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
        """Laadt het bestand als het bestaat, anders een leeg GeoDataFrame."""
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
        """
        Update of voegt een onderdeel toe aan de GeoJson. 
        Maakt gebruik van Geopandas voor efficiënte CRS transformaties en
        jouw array helper voor de diepte-bepaling.
        """
        from artof_utils.helpers import array
        from shapely.geometry import shape, Point, Polygon, LineString
        
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
                # --- NIEUW: Check of het al een lijst met Shapely objecten is ---
                elif hasattr(raw_list[0], 'geom_type'):
                    geoms = raw_list
                # -----------------------------------------------------------------
                else:
                    # --- HELPER: Diepte bepaling (uit array.py) ---
                    # Dit wordt nu alleen berekend als het écht om ruwe coördinaten gaat
                    depth = array.get_depth(geometries)

                    if depth == 1:
                        # Eén punt
                        geoms = [Point(raw_list)]
                    elif depth == 2:
                        # Lijn (bijv. traject)
                        if len(raw_list) == 1:
                            geoms = [Point(raw_list[0])]
                        else:
                            geoms = [LineString(raw_list)]
                    elif depth >= 3:
                        # Polygonen (bijv. geofence of tasks)
                        if depth == 3:
                            rings = raw_list
                        elif depth == 4:
                            rings = raw_list[0]
                        else:
                            rings = []

                        for ring in rings:
                            ring_arr = np.array(ring)
                            if len(ring_arr) >= 3:
                                # Ring sluiten als deze open is
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

            # 1. Maak de GeoDataFrame aan met de OORSPRONKELIJKE EPSG (input CRS)
            input_crs = f"EPSG:{epsg}" if epsg else "EPSG:4326"
            new_gdf = gpd.GeoDataFrame(
                {'name': [name] * len(geoms), 'type': [str(type)] * len(geoms)}, 
                geometry=geoms, 
                crs=input_crs
            )

        # --- EINDE OPBOUW ---

        # 2. Voeg extra metadata toe (bijv. implement details van de taak)
        if properties:
            for key, value in properties.items():
                new_gdf[key] = value

        # 3. NATIVE GEOPANDAS CRS TRANSFORMATIE
        # Als er een epsg is meegegeven (bijv. 32631 UTM), reken dit in 1 klap om naar 4326 (WGS84 GPS)
        if new_gdf.crs and new_gdf.crs.to_epsg() != 4326:
            new_gdf = new_gdf.to_crs(epsg=4326)

        # 4. Samenvoegen met de bestaande GeoDataFrame
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
            
            # Altijd de raster map checken
            raster_path = path.join(self.folder_path, "rasters")
            makedirs(raster_path, exist_ok=True)
                
            self.gdf.to_file(self.file_path, driver='GeoJSON')

    def delete(self, name: str):
        """
        Verwijdert een onderdeel uit de GDF en schoont bijbehorende bestanden op.
        """
        if self.gdf is None or self.gdf.empty:
            return

        # 1. Check of het item bestaat
        item_to_delete = self.gdf[self.gdf['name'] == name]
        if item_to_delete.empty:
            print(f"Item '{name}' niet gevonden in GeoJSON.")
            return

        # 2. Optioneel: Ruim raster bestanden op als die er zijn
        # We kijken of er een kolom 'raster_path' of 'name' is die we kunnen linken
        potential_raster = path.join(self.raster_path, f"{name}.tif")
        if path.exists(potential_raster):
            try:
                os.remove(potential_raster)
            except Exception as e:
                print(f"Kon raster voor {name} niet verwijderen: {e}")

        # 3. Filter de GDF (behoud alles behalve dit item)
        self.gdf = self.gdf[self.gdf['name'] != name]

        # 4. Opslaan
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