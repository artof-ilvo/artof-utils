from unittest import TestCase
from artof_utils.schemas.field import Fields, Field
from artof_utils.schemas.task import TaskInfo, HitchType, HitchName
from artof_utils.shapefile import GeomType
import json
from os import path
import numpy as np


class TestFields(TestCase):
    def test_load(self):
        # Arrange
        example = Field('example')
        # Act
        context = example.context
        # Assert - We checken nu of het een geldige GeoJSON FeatureCollection teruggeeft
        self.assertIn('features', context['traject_geometry'])

    def test_load_1(self):
        example = Field('example1')
        context = example.context
        self.assertIn('features', context['geofence_geometry'])

    def test_load_2(self):
        example = Field('test_tv115_drive_in')
        context = example.context
        self.assertIn('features', context['geofence_geometry'])

    def test_load_3(self):
        example = Field('test_veld_tv115')
        context = example.context
        self.assertIn('features', context['geofence_geometry'])

    def test_load_discrete(self):
        example = Field('example_discrete')
        task_info = TaskInfo(name='Task1', type='discrete', hitch=HitchName.HITCH_FB, implement='test_TV')
        geometries = [
            [[[50.0, 50.0], [50.0, 95.0], [55.0, 95.0], [55.0, 50.0]]],
            [[[60.0, 50.0], [60.0, 95.0], [65.0, 95.0], [65.0, 50.0]]]
        ]

        # Als de taak niet bestaat, voeg hem toe (in plaats van updaten wat een error geeft)
        if example.get_task('Task1') is None:
            example.add_task(task_info, geometries)
        else:
            example.update_task('Task1', geometries, task_info, epsg=4326)

        task = example.get_task('Task1')
        self.assertIsNotNone(task)
        self.assertEqual(task.name, 'Task1')
        
        # Check in de GeoDataFrame
        gdf_names = example.geo_data.gdf['name'].values
        self.assertIn('Task1', gdf_names)

    def test_select_field(self):
        new_field_name = 'test_field_select'
        fields = Fields()
        
        # Voor de zekerheid: als hij toevallig nog bestond van een vorige crash, gooi hem dan eerst weg
        if fields.exists(new_field_name):
            fields.current_field = "" # Zorg dat we hem mogen verwijderen
            fields.delete_field(new_field_name)

        # 1. SETUP: Maak een tijdelijk veld aan en forceer opslaan
        temp_field = Field(new_field_name)
        temp_field.geo_data.save() # DIT zorgt dat het bestand echt op de schijf komt
        
        try:
            # Zorg dat de Fields manager weet dat dit nieuwe bestand er is
            fields.refresh()
            
            # 2. ACT: Selecteer het veld via jouw manager
            fields.select_field(new_field_name)
            
            # 3. ASSERT: Controleer of het goed is gegaan
            self.assertTrue(fields.exists(new_field_name))
            self.assertTrue(path.exists(temp_field.geo_data.file_path))
            self.assertEqual(temp_field.name, new_field_name)
            
        finally:
            # 4. TEARDOWN: Dit blok wordt ALTIJD uitgevoerd, ook als de asserts hierboven falen!
            fields.current_field = ""  # Voorkom "is currently active" error bij verwijderen
            fields.delete_field(new_field_name)
            
            # Dubbele check via het object zelf voor de zekerheid
            if path.exists(temp_field.field_path):
                import shutil
                shutil.rmtree(temp_field.field_path, ignore_errors=True)

    def test_delete_field(self):
        new_field_name = 'test_field'
        fields = Fields()
        new_field = Field(new_field_name) 
        fields.delete_field(new_field.name)
        
        # Bestand zou weg moeten zijn
        self.assertFalse(path.exists(new_field.geo_data.file_path))
        self.assertFalse(fields.exists(new_field_name))

    def test_duplicate_field(self):
        fields = Fields()
        example = Field('example')
        field_new = fields.duplicate_field(example.name)
        
        self.assertTrue(fields.exists('example_copy'))
        # Controleer of het nieuwe GeoJSON bestand bestaat
        self.assertTrue(path.exists(field_new.geo_data.file_path))

        fields.delete_field(field_new.name)

    def test_create_new_field(self):
        # Arrange
        traject_coords = np.array([
            [50., 5.], [50., 95.], [55., 95.], [55., 5.]
        ])
        geofence_coords = np.array([
            [0., 0.], [0., 100.], [100., 100.], [100., 0.]
        ])

        task1_coords = np.array([[[10.0, 10.0], [10.0, 90.0], [20.0, 90.0], [20.0, 10.0]]])
        task2_coords = np.array([[[30.0, 10.0], [30.0, 90.0], [40.0, 90.0], [40.0, 10.0]]])

        field_new = Field('example_new')
        fields = Fields()
        
        # Act
        field_new.update_traject(traject_coords)
        field_new.update_geofence(geofence_coords)
        field_new.add_task(TaskInfo(name='task1', type=HitchType.HITCH, hitch=HitchName.HITCH_FB), task1_coords)
        field_new.add_task(TaskInfo(name='task2', type=HitchType.CONTINUOUS, hitch=HitchName.HITCH_FB), task2_coords)
        field_new.add_new_task()

        # Assert: Check of bestand bestaat
        self.assertTrue(path.exists(field_new.geo_data.file_path))
        
        # Haal de namen in de GeoDataFrame op
        names_in_gdf = field_new.geo_data.gdf['name'].values
        
        self.assertIn('geofence', names_in_gdf)
        self.assertIn('traject', names_in_gdf)
        
        for task_name in ['task1', 'task2']:
            task = field_new.get_task(task_name)
            self.assertIsNotNone(task)
            self.assertIn(task.name, names_in_gdf)
            
            # Check of het geometrie type Polygon is
            geom_types = field_new.geo_data.gdf[field_new.geo_data.gdf['name'] == task.name].geom_type.values
            self.assertTrue(all('Polygon' in t for t in geom_types))

        task_name = [task.name for task in field_new.tasks]
        self.assertEqual(set(task_name), {'task1', 'task2', 'Task1'})

        fields.delete_field(field_new.name)

    def test_rename_field(self):
        new_name = 'example_new_name'
        field = Field('example')
        fields = Fields()
        renamed_field = field.rename(new_name)

        self.assertTrue(Fields().exists(new_name))
        
        # Test op de nieuwe .name property ipv .info.name
        self.assertEqual(renamed_field.name, new_name)
        
        renamed_field.rename('example')