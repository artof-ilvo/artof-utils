import pandas as pd
from unittest import TestCase
from artof_utils.schemas.field import Fields, Field
from artof_utils.schemas.task import TaskInfo, HitchType, HitchName
from os import path
import numpy as np


class TestFields(TestCase):
    def test_load(self):
        # Arrange
        example = Field('example')
        # Act
        context = example.context
        # Assert
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
        geometries = [[[3.7740, 50.9800], [3.7740, 50.9805], [3.7742, 50.9805], [3.7742, 50.9800], [3.7740, 50.9800]]]
        

        if example.get_task('Task1') is None:
            example.add_task(task_info, geometries)
        else:
            example.update_task('Task1', geometries, task_info, epsg=4326)

        task = example.get_task('Task1')
        self.assertIsNotNone(task)
        self.assertEqual(task.name, 'Task1')
        
        gdf_names = example.geo_data.gdf['name'].values
        self.assertIn('Task1', gdf_names)

        #example.remove_task('Task1')

    def test_select_field(self):
        new_field_name = 'test_field_select'
        fields = Fields()
    
        if fields.exists(new_field_name):
            fields.current_field = "" # for deleting
            fields.delete_field(new_field_name)

        temp_field = Field(new_field_name)
        temp_field.geo_data.save() 
        
        try:
            fields.refresh()
            
            fields.select_field(new_field_name)
            
            self.assertTrue(fields.exists(new_field_name))
            self.assertTrue(path.exists(temp_field.geo_data.file_path))
            self.assertEqual(temp_field.name, new_field_name)
            
        finally:
            fields.current_field = ""  # for deleting
            fields.delete_field(new_field_name)
            
            if path.exists(temp_field.field_path):
                import shutil
                shutil.rmtree(temp_field.field_path, ignore_errors=True)

    def test_delete_field(self):
        new_field_name = 'test_field'
        fields = Fields()
        new_field = Field(new_field_name) 
        fields.delete_field(new_field.name)
        
        self.assertFalse(path.exists(new_field.geo_data.file_path))
        self.assertFalse(fields.exists(new_field_name))

    def test_duplicate_field(self):
        fields = Fields()
        example = Field('example')
        field_new = fields.duplicate_field(example.name)
        
        self.assertTrue(fields.exists('example_copy'))
        self.assertTrue(path.exists(field_new.geo_data.file_path))

        fields.delete_field(field_new.name)

    def test_create_new_field(self):
        # Arrange
        traject_coords = np.array([
            [50., 5.], [50., 95.], [55., 95.], [55., 5.]
        ])
        geofence_coords = np.array([
            [0., 0.], [0., 100.], [100., 100.], [100., 0.], [0., 0.]
        ])

        task1_coords = np.array([[[10.0, 10.0], [10.0, 90.0], [20.0, 90.0], [20.0, 10.0]]])
        task2_coords = np.array([[[30.0, 10.0], [30.0, 90.0], [40.0, 90.0], [40.0, 10.0]]])

        field_new = Field('example_new')
        fields = Fields()
        
        # Act
        field_new.update_traject(traject_coords)
        field_new.update_geofence(geofence_coords)
        field_new.add_task(TaskInfo(name='task1', type=HitchType.HITCH, hitch=HitchName.HITCH_FB), task1_coords)
        field_new.add_task(TaskInfo(name='task2', type=HitchType.DISCRETE, hitch=HitchName.HITCH_FB), task2_coords)
        field_new.add_new_task()

        # Assert
        self.assertTrue(path.exists(field_new.geo_data.file_path))
        
        names_in_gdf = field_new.geo_data.gdf['name'].values
        
        self.assertIn('geofence', names_in_gdf)
        self.assertIn('traject', names_in_gdf)
        
        for task_name in ['task1', 'task2']:
            task = field_new.get_task(task_name)
            self.assertIsNotNone(task)
            # Controleer of de rij in de GDF de juiste metadata heeft
            task_row = field_new.geo_data.gdf[field_new.geo_data.gdf['name'] == task.name].iloc[0]
            
            # De 'type' kolom moet nu 'raster' zijn
            self.assertEqual(task_row['type'], 'raster')
            
            # De geometrie moet None zijn
            self.assertTrue(pd.isna(task_row['geometry']) or task_row['geometry'] is None)
            
            # Er moet een verwijzing zijn naar het .tif bestand
            self.assertTrue(task_row['raster_source'].endswith('.tif'))

        task_name = [task.name for task in field_new.tasks]
        self.assertEqual(set(task_name), {'task1', 'task2', 'Task1'})

        #fields.delete_field(field_new.name)

    def test_rename_field(self):
        new_name = 'example_new_name'
        field = Field('example')
        fields = Fields()
        renamed_field = field.rename(new_name)

        self.assertTrue(Fields().exists(new_name))
        
        self.assertEqual(renamed_field.name, new_name)
        
        renamed_field.rename('example')