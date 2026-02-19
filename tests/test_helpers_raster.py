from unittest import TestCase
import os
import shutil
from shapely.geometry import Polygon
from artof_utils.helpers.raster import Raster

class TestHelperRaster(TestCase):
    
    def test_create_geotiff_creation(self):
        # Arrange
        test_dir = "temp_raster_test_helper"
        os.makedirs(test_dir, exist_ok=True)
        output_path = os.path.join(test_dir, "test.tif")
        geom = Polygon([(0,0), (0,10), (10,10), (10,0), (0,0)])
        bounds = (0, 0, 10, 10)
        
        try:
            # Act
            Raster.create_geotiff(
                geometry=geom,
                bounds=bounds,
                resolution=1.0, 
                output_path=output_path,
                crs="EPSG:4326"
            )
            
            # Assert
            self.assertTrue(os.path.exists(output_path))
            
        finally:
            # Cleanup
            if os.path.exists(test_dir):
                shutil.rmtree(test_dir)