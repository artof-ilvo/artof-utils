from unittest import TestCase
import os
import shutil
from artof_utils.schemas.task import Task, TaskInfo, HitchType, HitchName
from artof_utils.geojson import GeoJson
from artof_utils.paths import fields

class TestTask(TestCase):
    def test_update_triggers_raster_generation(self):
        # Arrange
        path = os.path.join(fields, "example_task_test")
        geo_data = GeoJson(path)
        task_info = TaskInfo(
            name="Task1", 
            type=HitchType.DISCRETE, 
            hitch=HitchName.HITCH_FB,
        )
        task = Task(task_info, geo_data)
        
        # Input data (lijst van punten)
        points = [[10, 10], [20, 20]]
        
        # Act
        task.update(points)
        
        # Assert
        # 1. Check of bestand bestaat
        expected_tif = os.path.join(path, "rasters", "Task1.tif")
        self.assertTrue(os.path.exists(expected_tif))
        
        # 2. Check of GeoJson de juiste properties heeft
        geo_data.load()
        row = geo_data.gdf[geo_data.gdf['name'] == "Task1"].iloc[0]
        self.assertEqual(row.hitch_name, HitchName.HITCH_FB.value)
        self.assertEqual(row.type, 'raster')

        geo_data.delete("example_task_test")  # Opruimen na de test