from unittest import TestCase
import os
import shutil
from artof_utils.paths import fields
import geopandas as gpd
from shapely.geometry import Point, Polygon
from artof_utils.geojson import GeoJson
from artof_utils import paths  

class TestGeoJson(TestCase):
    
    def setUp(self):
        """
        Wordt uitgevoerd voor elke test.
        We maken een unieke testmap binnen de standaard fields locatie.
        """
        path_test = os.path.join(fields, "example_task_test")

        if os.path.exists(path_test):
            shutil.rmtree(path_test)
        os.makedirs(path_test, exist_ok=True)
        self.test_dir = path_test
        self.test_filename = "data"

    def tearDown(self):
        """Opruimen na de test."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_initialization(self):
        geojson = GeoJson(self.test_dir, self.test_filename)
        self.assertIsInstance(geojson.gdf, gpd.GeoDataFrame)
        # Check of de cruciale 'name' kolom bestaat (via de nieuwe load fix)
        self.assertIn('name', geojson.gdf.columns)

    def test_update_vector_point(self):
        geojson = GeoJson(self.test_dir, self.test_filename)
        name = "home_point"
        geojson.update([3.7, 51.0], name, type="Point")
        
        self.assertEqual(len(geojson.gdf), 1)
        self.assertEqual(geojson.gdf.iloc[0]['name'], name)

    def test_save_as_raster(self):
        geojson = GeoJson(self.test_dir, self.test_filename)
        name = "raster_task"
        geom = [(0,0), (0,10), (10,10), (10,0), (0,0)]
        
        # Act
        geojson.save_as_raster(name, geom, resolution=0.5, properties={"hitch_name": "sprayer"})

        # Assert
        expected_path = os.path.join(self.test_dir, "rasters", f"{name}.tif")
        self.assertTrue(os.path.exists(expected_path))
        
        # Check GDF referentie
        row = geojson.gdf[geojson.gdf['name'] == name].iloc[0]
        self.assertIsNone(row.geometry)
        self.assertEqual(row.raster_source, f"rasters/{name}.tif")

    def test_delete_raster_files(self):
        geojson = GeoJson(self.test_dir, self.test_filename)
        name = "test_delete"
        
        # 1. Voeg EERST een geofence toe (het kader van ons veld)
        # Bijvoorbeeld een veld van 10x10 meter
        geofence_coords = [(0,0), (0,10), (10,10), (10,0), (0,0)]
        geojson.update(geofence_coords, "geofence", type="Polygon")
        
        # 2. Voeg nu een taak toe (mag nu wel een Point zijn!)
        # Omdat de geofence er is, wordt het raster 10x10m groot, 
        # ook al is de taak zelf maar één punt.
        geojson.save_as_raster(name, Point(5,5), resolution=0.1)
        
        tif_path = os.path.join(self.test_dir, "rasters", f"{name}.tif")
        self.assertTrue(os.path.exists(tif_path), "Het raster-bestand zou nu aangemaakt moeten zijn")
        
        # Act
        geojson.delete(name)
        
        # Assert
        self.assertFalse(os.path.exists(tif_path), "Het raster-bestand moet fysiek verwijderd zijn")
        self.assertTrue(name not in geojson.gdf['name'].values, "De referentie moet uit de GDF zijn")