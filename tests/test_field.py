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
        # Load existing field
        example = Field('example')
        # Act
        context = example.context
        # Assert
        self.assertFalse(context['traject_geometry']['hasZ'])

    def test_load_1(self):
        # Arrange
        # Load existing field
        example = Field('example1')
        # Act
        context = example.context
        # Assert
        self.assertFalse(context['geofence_geometry']['hasZ'])

    def test_load_2(self):
        # Arrange
        # Load existing field
        example = Field('test_tv115_drive_in')
        # Act
        context = example.context
        # Assert
        self.assertFalse(context['geofence_geometry']['hasZ'])

    def test_load_3(self):
        # Arrange
        # Load existing field
        example = Field('test_veld_tv115')
        # Act
        context = example.context
        # Assert
        self.assertFalse(context['geofence_geometry']['hasZ'])


    def test_load_discrete(self):
        # Arrange
        # Load existing field
        example = Field('example_discrete')
        task_info = TaskInfo(name='Task1', type='discrete', implement='penetrometer', hitch='RB')
        geometries = [[50.98025314667279, 3.774201817882501], [50.98040955139628, 3.7740730721325884], [50.98068562130093, 3.7738446381681716], [50.98076002267542, 3.773785085870838], [50.98073868953959, 3.7738332178084626], [50.980462629247924, 3.774060204906186], [50.98024215091789, 3.7742410751408064], [50.98028717919914, 3.774227893352885], [50.98050291227711, 3.7740737199976837], [50.98049982633975, 3.7741257733643296], [50.980606381292304, 3.7741087297280322], [50.98043429187918, 3.7742259980617856], [50.980598264702074, 3.7740926738451805], [50.980496736769894, 3.774247299568263]]
        example.update_task('Task1', geometries, task_info, epsg=4326)
        # Act
        context = example.context
        task_context = example.tasks[0].context
        # Assert
        self.assertTrue('points' in context['task_geometries'][0]['geometry'])
        self.assertTrue(example.tasks[0].shp_task.geom_type == GeomType.POINT)
        self.assertTrue(task_context['implement'] == 'penetrometer')

    def test_select_field(self):
        # Arrange
        # Create new field
        new_field = Field('field_new')
        # Act
        Fields().select_field(new_field.name)
        # Assert
        self.assertEqual(Fields().current_field, new_field.name)
        self.assertTrue(path.exists(new_field.info_file_path))
        from artof_utils.redis_instance import redis_server
        # Set 'field_updated' back to False. This is to indicate that the field was updated.
        # If no test, the cpp 'FieldManager' would otherwise do this
        redis_server.set_value("pc.field.updated", False)
        # select example again
        Fields().select_field('example')

    def test_delete_field(self):
        # Arrange
        # Create new field
        new_field = Field('field_new')
        # Act
        Fields().delete_field(new_field.name)
        # Assert
        self.assertFalse(path.exists(new_field.info_file_path))

    def test_duplicate_field(self):
        # Arrange
        fields = Fields()
        Fields().select_field('example_discrete')
        # Act
        field_new = fields.duplicate_field(fields.current_field)
        fields_new = Fields()
        # Assert
        self.assertIn('_copy', field_new.name)
        self.assertIn(field_new.name, fields_new.fields)
        with open(field_new.info_file_path, 'r') as f:
            info = json.load(f)
            self.assertEqual(field_new.name, info['name'])

    def test_create_new_field(self):
        # Arrange
        geofence_coords = [[[0.0, 0.0], [0.0, 100.00], [100.0, 100.0], [100.0, 0.0]]]
        traject_coords = np.array([[50.0, 5.0], [50.0, 95.00], [55.0, 95.0], [55.0, 5.0]])
        task1_coords = np.array([[10.0, 10.0], [10.0, 90.00], [90.0, 90.0], [90.0, 10.0], [10.0, 10.0]])
        task2_coords = np.array([[[10.0, 10.0], [10.0, 90.00], [90.0, 90.0], [90.0, 10.0]]])

        field_new = Field('example_new')
        # Be sure no tasks in the system for this field
        task_names = [task.name for task in field_new.tasks]
        for task_name in task_names:
            field_new.remove_task(task_name)

        # Act
        field_new.update_traject(traject_coords)
        field_new.update_geofence(geofence_coords)
        field_new.add_task(TaskInfo(name='task1', type=HitchType.HITCH, hitch=HitchName.HITCH_FB), task1_coords)
        field_new.add_task(TaskInfo(name='task2', type=HitchType.CONTINUOUS, hitch=HitchName.HITCH_FB), task2_coords)
        field_new.add_new_task()
        # Assert
        self.assertTrue(path.exists(field_new.shp_geofence.file_path))
        self.assertTrue(path.exists(field_new.shp_traject.file_path))
        for task_name in ['task1', 'task2']:
            task = field_new.get_task(task_name)
            self.assertTrue(path.exists(task.shp_task.file_path))
            self.assertEqual(task.shp_task.get_geom_type(), GeomType.POLYGON)

        task_name = [task.name for task in field_new.tasks]
        self.assertEqual(set(task_name), {'task1', 'task2', 'task3'})

    def test_rename_field(self):
        # Arrange
        orig_name = 'example_name_new'
        new_name = 'example_name_renamed_new'
        Fields().delete_field(new_name)
        # Act
        field = Field(orig_name)
        renamed_field = field.rename(new_name)
        # Assert
        self.assertEqual(renamed_field.name, new_name)
