import geopandas as gpd
import pandas as pd
from typing import Union
from shapely.geometry import Polygon, MultiPoint
import ast

from artof_utils.schemas.task import Task

class TaskManager:
    def __init__(self, task_info: Task, field_gdf: gpd.GeoDataFrame = None):
        """
        De manager koppelt de pure taak-data aan het wiskundige canvas (het GeoDataFrame).
        """
        self.info = task_info
        self.gdf = field_gdf if field_gdf is not None else gpd.GeoDataFrame()

    def __eq__(self, other):
        return self.info.name == other.info.name

    def __hash__(self):
        return hash(self.info.name)

    def __lt__(self, other):
        return self.info.name < other.info.name

    def __gt__(self, other):
        return self.info.name > other.info.name

    @property
    def name(self):
        return self.info.name
    
    def update(self, geometry: Union[Polygon, MultiPoint]) -> gpd.GeoDataFrame:
        """
        Voegt de taak-geometrie toe of updatet deze in het GeoDataFrame.
        Verwacht een puur Shapely object (Polygon of MultiPoint) van de backend!
        Geeft het aangepaste dataframe terug aan de backend.
        """
        if not self.gdf.empty and 'name' in self.gdf.columns:
            mask = self.gdf['name'] == self.name
        else:
            mask = pd.Series([False])

        if mask.any():
            idx = self.gdf[mask].index[0]
            self.gdf.at[idx, 'geometry'] = geometry
            self.gdf.at[idx, 'type'] = self.info.type
            self.gdf.at[idx, 'hitch_type'] = self.info.hitch_type.value
            self.gdf.at[idx, 'hitch_name'] = self.info.hitch_name.value
            self.gdf.at[idx, 'implement'] = self.info.implement
            self.gdf.at[idx, 'raster_source'] = self.info.raster_source
            self.gdf.at[idx, 'overlay_source'] = self.info.overlay_source
            self.gdf['bounds'] = self.gdf.get('bounds', pd.Series(dtype=object))
            self.gdf.at[idx, 'bounds'] = self.info.bounds
        else:
            new_row = gpd.GeoDataFrame({
                'name': [self.name], 
                'type': [self.info.type],
                'hitch_type': [self.info.hitch_type.value],
                'hitch_name': [self.info.hitch_name.value],
                'implement': [self.info.implement],
                'raster_source': [self.info.raster_source],
                'overlay_source': [self.info.overlay_source],
                'bounds': [self.info.bounds]
            }, geometry=[geometry], crs=self.gdf.crs if not self.gdf.empty else "EPSG:4326")
            
            self.gdf = pd.concat([self.gdf, new_row], ignore_index=True)

        return self.gdf

    def delete(self) -> gpd.GeoDataFrame:
        """
        Verwijdert de taak uit het GeoDataFrame.
        Geeft het opgeschoonde dataframe terug.
        """
        if not self.gdf.empty and 'name' in self.gdf.columns:
            self.gdf = self.gdf[self.gdf['name'] != self.name]
        return self.gdf

    def update_info(self, new_info: Task) -> gpd.GeoDataFrame:
        """
        Update enkel de metadata van de taak in het dataframe.
        """
        self.info = new_info
        
        if not self.gdf.empty and 'name' in self.gdf.columns:
            mask = self.gdf['name'] == self.name
            if mask.any():
                idx = self.gdf[mask].index[0]
                self.gdf.at[idx, 'type'] = self.info.type
                self.gdf.at[idx, 'hitch_type'] = self.info.hitch_type.value
                self.gdf.at[idx, 'hitch_name'] = self.info.hitch_name.value
                self.gdf.at[idx, 'implement'] = self.info.implement
                self.gdf.at[idx, 'raster_source'] = self.info.raster_source
                self.gdf.at[idx, 'overlay_source'] = self.info.overlay_source
                
                self.gdf['bounds'] = self.gdf.get('bounds', pd.Series(dtype=object))
                self.gdf.at[idx, 'bounds'] = self.info.bounds
                
        return self.gdf

    @property
    def context(self):
        """
        Exporteert de task inclusief de huidige geometrie en Leaflet overlay-data.
        """
        geom = None
        overlay_src = self.info.overlay_source
        bounds_raw = self.info.bounds

        if not self.gdf.empty and 'name' in self.gdf.columns:
            row = self.gdf[self.gdf['name'] == self.name]
            if not row.empty:
                geom = row.geometry.iloc[0]
                if 'overlay_source' in row.columns and pd.notna(row['overlay_source'].iloc[0]):
                    overlay_src = row['overlay_source'].iloc[0]
                if 'bounds' in row.columns and pd.notna(row['bounds'].iloc[0]):
                    bounds_raw = row['bounds'].iloc[0]

        if isinstance(bounds_raw, str):
            try:
                bounds_raw = ast.literal_eval(bounds_raw)
            except (ValueError, SyntaxError):
                bounds_raw = None

        # shapley bounds to Leaflet bounds: [[miny, minx], [maxy, maxx]]
        image_bounds = None
        if bounds_raw and len(bounds_raw) == 4:
            minx, miny, maxx, maxy = bounds_raw
            image_bounds = [[miny, minx], [maxy, maxx]]

        return {
            'name': self.name,
            'type': self.info.type,
            'hitch_type': self.info.hitch_type.value,
            'hitch_name': self.info.hitch_name.value,
            'implement': self.info.implement,
            'raster_source': self.info.raster_source,
            'overlay_source': overlay_src,       
            'image_bounds': image_bounds,        
            'geometry': geom.__geo_interface__ if geom else None
        }