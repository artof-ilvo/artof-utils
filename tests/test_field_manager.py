import geopandas as gpd
import pandas as pd
from unittest import TestCase
from shapely.geometry import Polygon, LineString

from artof_utils.field_manager import FieldManager
from artof_utils.schemas.task import Task, HitchType, HitchName


class TestFieldManager(TestCase):

    def test_init_met_bestaand_geodataframe(self):
        """Test of de FieldManager een GDF van de backend perfect leest (de nieuwe flow)."""
        # 1. Mock de data alsof die vers uit de database komt
        mock_gdf = gpd.GeoDataFrame({
            'name': ['geofence', 'Task1'],
            'type': ['geofence', 'task'],
            'hitch_type': [None, HitchType.HITCH.value],
            'hitch_name': [None, HitchName.HITCH_FB.value],
            'implement': [None, 'Ploeg']
        }, geometry=[
            Polygon([[0,0], [10,0], [10,10], [0,10], [0,0]]),
            Polygon([[1,1], [2,1], [2,2], [1,2], [1,1]])
        ], crs="EPSG:4326")

        # 2. Geef het GDF direct aan de manager
        veld = FieldManager(name='BestaandVeld', field_gdf=mock_gdf)

        # 3. Controles
        self.assertEqual(len(veld.task_managers), 1)
        taak = veld.get_task('Task1')
        self.assertIsNotNone(taak)
        self.assertEqual(taak.info.implement, 'Ploeg')

        # 4. Controleer een stateless actie
        vernieuwd_gdf = veld.remove_task('Task1')
        self.assertEqual(len(vernieuwd_gdf), 1)
        self.assertNotIn('Task1', vernieuwd_gdf['name'].values)

    def test_context_generation(self):
        """Vervangt de oude test_load... checks door in-memory dict checks."""
        veld = FieldManager('example_context')
        geofence_poly = Polygon([[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]])
        veld.update_geofence(geofence_poly)

        context = veld.context
        self.assertIsNotNone(context['geofence_geometry'])
        self.assertEqual(context['name'], 'example_context')

    def test_task_management(self):
        """Test in-memory task toevoegen en updaten met pure Shapely vormen."""
        veld = FieldManager('example_discrete')
        nieuwe_taak = Task(name='Task1', type=HitchType.DISCRETE, hitch=HitchName.HITCH_FB, implement='test_TV')
        taak_poly = Polygon([[3.7740, 50.9800], [3.7740, 50.9805], [3.7742, 50.9805], [3.7742, 50.9800], [3.7740, 50.9800]])

        # Toevoegen
        if veld.get_task('Task1') is None:
            veld.add_task(nieuwe_taak, taak_poly)

        # Update
        geupdate_taak = Task(name='Task1', type=HitchType.DISCRETE, hitch=HitchName.HITCH_FB, implement='test_TV_geupdate')
        veld.update_task('Task1', geometry=taak_poly, task_info=geupdate_taak)

        # Asserts
        task_manager = veld.get_task('Task1')
        self.assertIsNotNone(task_manager)
        self.assertEqual(task_manager.name, 'Task1')

        gdf_names = veld.gdf['name'].values
        self.assertIn('Task1', gdf_names)

        task_row = veld.gdf[veld.gdf['name'] == 'Task1'].iloc[0]
        self.assertEqual(task_row['implement'], 'test_TV_geupdate')

    def test_create_new_field_elements(self):
        """Test het toevoegen van alle veld-elementen aan het DataFrame."""
        traject_line = LineString([[50., 5.], [50., 95.], [55., 95.], [55., 5.]])
        geofence_poly = Polygon([[0., 0.], [0., 100.], [100., 100.], [100., 0.], [0., 0.]])
        task1_poly = Polygon([[10.0, 10.0], [10.0, 90.0], [20.0, 90.0], [20.0, 10.0]])
        task2_poly = Polygon([[30.0, 10.0], [30.0, 90.0], [40.0, 90.0], [40.0, 10.0]])

        veld = FieldManager('example_new')

        # Act
        veld.update_traject(traject_line)
        veld.update_geofence(geofence_poly)
        veld.add_task(Task(name='task1', type=HitchType.HITCH, hitch=HitchName.HITCH_FB), task1_poly)
        veld.add_task(Task(name='task2', type=HitchType.DISCRETE, hitch=HitchName.HITCH_FB), task2_poly)
        veld.add_new_task() # Voegt auto-gen 'Task1' toe zonder coords

        # Assert: We checken het GDF, niet de harde schijf
        names_in_gdf = veld.gdf['name'].values

        self.assertIn('geofence', names_in_gdf)
        self.assertIn('traject', names_in_gdf)
        self.assertIn('task1', names_in_gdf)
        self.assertIn('task2', names_in_gdf)

        task_names = [tm.name for tm in veld.task_managers]
        self.assertEqual(set(task_names), {'task1', 'task2', 'Task1'})

        task_row = veld.gdf[veld.gdf['name'] == 'task1'].iloc[0]
        self.assertEqual(task_row['type'], 'task')
        self.assertFalse(pd.isna(task_row['geometry']))

    def test_rename_field(self):
        """Test of de string property update werkt."""
        new_name = 'example_new_name'
        veld = FieldManager('example')

        veld.rename(new_name)
        self.assertEqual(veld.name, new_name)