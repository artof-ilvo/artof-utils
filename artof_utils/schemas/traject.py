from pydantic import BaseModel, ConfigDict
import json
from typing import Union
import numpy as np
import geopandas as gpd
from artof_utils.geojson import GeoJson

class Traject(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    geo_data: GeoJson

    def __init__(self, geo_data: GeoJson):

        super().__init__(geo_data=geo_data)

    def update(self, geometries: Union[list, np.ndarray, gpd.GeoDataFrame, None] = None, epsg: int = 0):
        self.geo_data.update(
            geometries, 
            name="traject", 
            type="traject", 
            epsg=epsg
        )

    def delete(self):
        self.geo_data.delete("traject")
        
    @property
    def context(self):
        """Haalt de traject geometrie op voor de webapp."""
        if not self.exists:
            return {}
            
        traject_gdf = self.geo_data.gdf[self.geo_data.gdf['name'] == 'traject']
        return json.loads(traject_gdf.to_json())
    
    @property
    def exists(self) -> bool:
        """Check of er al een traject-laag in de GeoJSON staat."""
        if self.geo_data.gdf is None or self.geo_data.gdf.empty:
            return False
        return not self.geo_data.gdf[self.geo_data.gdf['name'] == 'traject'].empty