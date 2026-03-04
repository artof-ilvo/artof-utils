import geopandas as gpd
from unittest import TestCase
from shapely.geometry import MultiPoint, Polygon

from artof_utils.task_manager import TaskManager
from artof_utils.schemas.task import Task, HitchType, HitchName

class TestTask(TestCase):
    
    def test_task_update_in_memory(self):
        """Test of een taak correct wordt toegevoegd aan het in-memory GeoDataFrame."""
        # 1. ARRANGE: Geen bestanden of paden meer! Puur datamodel.
        task_info = Task(
            name="Task1",
            type=HitchType.DISCRETE,
            hitch=HitchName.HITCH_FB,
            implement="Onkruidsteker"
        )
        
        manager = TaskManager(task_info=task_info)
        
        # We voeren nu pure Shapely wiskunde in, geen rauwe lijstjes meer.
        punten = MultiPoint([[10, 10], [20, 20]])
        
        # 2. ACT
        vernieuwd_gdf = manager.update(punten)
        
        # 3. ASSERTS
        # Controleer of de rij is aangemaakt
        self.assertEqual(len(vernieuwd_gdf), 1)
        
        # Haal de rij van deze taak op uit het GeoDataFrame
        row = vernieuwd_gdf[vernieuwd_gdf['name'] == "Task1"].iloc[0]
        
        # Controleer of alle metadata netjes als kolommen is weggeschreven
        self.assertEqual(row['hitch_name'], HitchName.HITCH_FB.value)
        self.assertEqual(row['type'], 'task')
        self.assertEqual(row['implement'], 'Onkruidsteker')
        
        # De geometrie moet nu echt een Shapely vorm zijn in het dataframe
        self.assertEqual(row['geometry'].geom_type, 'MultiPoint')

    def test_task_delete(self):
        """Test of de taak zichzelf netjes uit het GeoDataFrame wist."""
        task_info = Task(name="TaakOmTeWissen")
        manager = TaskManager(task_info=task_info)
        
        # Voeg een vorm toe
        manager.update(Polygon([[0,0], [1,0], [1,1], [0,1], [0,0]]))
        self.assertEqual(len(manager.gdf), 1) # Rij is er
        
        # Act
        vernieuwd_gdf = manager.delete()
        
        # Assert
        self.assertTrue(vernieuwd_gdf.empty) # Rij is weg!

    def test_task_update_info(self):
        """Test of we de metadata van een bestaande taak kunnen overschrijven."""
        task_info = Task(name="Task1", implement="Oude_Ploeg")
        manager = TaskManager(task_info=task_info)
        manager.update(MultiPoint([[0,0]]))
        
        # Maak nieuwe info en update
        nieuwe_info = Task(name="Task1", implement="Nieuwe_Zaaier")
        manager.update_info(nieuwe_info)
        
        # Check in het GDF
        row = manager.gdf[manager.gdf['name'] == "Task1"].iloc[0]
        self.assertEqual(row['implement'], "Nieuwe_Zaaier")