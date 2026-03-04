# artof_utils/tasks.py

import geopandas as gpd
import pandas as pd
from typing import Union
from shapely.geometry import Polygon, MultiPoint

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
            self.gdf.loc[mask, 'geometry'] = geometry
            self.gdf.loc[mask, 'hitch_type'] = self.info.type.value
            self.gdf.loc[mask, 'hitch_name'] = self.info.hitch.value
            self.gdf.loc[mask, 'implement'] = self.info.implement
        else:
            new_row = gpd.GeoDataFrame({
                'name': [self.name], 
                'type': ['task'],
                'hitch_type': [self.info.type.value],
                'hitch_name': [self.info.hitch.value],
                'implement': [self.info.implement]
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
                self.gdf.loc[mask, 'hitch_type'] = self.info.type.value
                self.gdf.loc[mask, 'hitch_name'] = self.info.hitch.value
                self.gdf.loc[mask, 'implement'] = self.info.implement
                
        return self.gdf

    @property
    def context(self):
        """
        Exporteert de task inclusief de huidige geometrie voor weergave in de frontend.
        """
        geom = None
        if not self.gdf.empty and 'name' in self.gdf.columns:
            row = self.gdf[self.gdf['name'] == self.name]
            if not row.empty:
                geom = row.geometry.iloc[0]

        return {
            'name': self.name,
            'type': self.info.type.value,
            'hitch': self.info.hitch.value,
            'implement': self.info.implement,
            'geometry': geom.__geo_interface__ if geom else None
        }