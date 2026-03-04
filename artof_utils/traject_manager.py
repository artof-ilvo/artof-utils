import geopandas as gpd
import pandas as pd
from typing import Union
from shapely.geometry import LineString, MultiLineString

from artof_utils.schemas.traject import Traject

class TrajectManager:
    def __init__(self, field_gdf: gpd.GeoDataFrame = None):
        """
        Links the pure traject data to the mathematical canvas (the GeoDataFrame).
        """
        self.info = Traject() 
        self.gdf = field_gdf if field_gdf is not None else gpd.GeoDataFrame()

    def update_geometry(self, geometry: Union[LineString, MultiLineString]) -> gpd.GeoDataFrame:
        """
        overwrite the traject geometry in the GeoDataFrame. Expects a pure Shapely object from the backend!
        Returns the updated dataframe back to the backend.
        """
        if not self.gdf.empty and 'name' in self.gdf.columns:
            mask = self.gdf['name'] == self.info.name
        else:
            mask = pd.Series([False])

        if mask.any():
            self.gdf.loc[mask, 'geometry'] = geometry
        else:
            new_row = gpd.GeoDataFrame({
                'name': [self.info.name], 
                'type': ['LineString']
            }, geometry=[geometry], crs=self.gdf.crs if not self.gdf.empty else "EPSG:4326")
            
            self.gdf = pd.concat([self.gdf, new_row], ignore_index=True)

        return self.gdf

    def delete(self) -> gpd.GeoDataFrame:
        """
        delete the traject geometry from the GeoDataFrame. Expects a pure Shapely object from the backend!
        Returns the updated dataframe back to the backend.
        """
        if not self.gdf.empty and 'name' in self.gdf.columns:
            self.gdf = self.gdf[self.gdf['name'] != self.info.name]
        return self.gdf

    @property
    def exists(self) -> bool:
        """Controleert razendsnel of het traject al getekend is in dit dataframe."""
        if self.gdf is None or self.gdf.empty or 'name' not in self.gdf.columns:
            return False
        return not self.gdf[self.gdf['name'] == self.info.name].empty

    @property
    def context(self) -> dict:
        """
        gets the traject geometry in GeoJSON format. Expects a pure Shapely object from the backend!
        """
        if not self.exists:
            return {}
            
        row = self.gdf[self.gdf['name'] == self.info.name]
        geom = row.geometry.iloc[0]
        
        return geom.__geo_interface__