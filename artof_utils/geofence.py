from artof_utils.shapefile import Shapefile
import json

class Geofence(Shapefile):
    def __init__(self, folder_path):
        super().__init__(folder_path)
        # Assert when gdf is no Polygon
        assert self.geom_type == 'Polygon', "Geofence must be a Polygon"

    def buffer(self, distance: float, **kwargs):
        gdf = self.gdf_mods[-1].copy() if len(self.gdf_mods) > 0 else self.gdf.copy()
        gdf.geometry = gdf.geometry.buffer(distance, **kwargs)
        return gdf


