import geopandas as gpd
import pandas as pd
from typing import Optional, Union

# Strikte Shapely types voor de input!
from shapely.geometry import Polygon, LineString, MultiPoint

from artof_utils.schemas.field import Field  
from artof_utils.schemas.task import Task, HitchType, HitchName
from artof_utils.schemas.traject import Traject

from artof_utils.traject_manager import TrajectManager
from artof_utils.task_manager import TaskManager

import json

class FieldManager:
    def __init__(self, name: str, field_gdf: Optional[gpd.GeoDataFrame] = None):
        """
        De FieldManager is de hoofdmanager voor een veld. 
        Krijgt een in-memory GeoDataFrame direct van de backend.
        """
        self.info = Field(name=name)
        self.gdf = field_gdf if field_gdf is not None else gpd.GeoDataFrame()
        
        self.traject_manager = TrajectManager(self.gdf)
        self.task_managers: list[TaskManager] = []
        self._parse_tasks()

    def _parse_tasks(self):
        """Kijkt of er al taken in het GDF zitten en maakt er TaskManagers van."""
        self.task_managers = []
        if not self.gdf.empty and 'type' in self.gdf.columns:
            task_rows = self.gdf[self.gdf['type'] == 'task']
            
            for _, row in task_rows.iterrows():
                t_info = Task(
                    name=row.get('name', 'Unknown'),
                    type=row.get('hitch_type', HitchType.HITCH),
                    hitch=row.get('hitch_name', HitchName.HITCH_FB),
                    implement=row.get('implement', '')
                )
                self.task_managers.append(TaskManager(task_info=t_info, field_gdf=self.gdf))

    def _sync_gdfs(self):
        """Zorgt dat de sub-managers altijd naar de nieuwste versie van het GDF wijzen."""
        self.traject_manager.gdf = self.gdf
        for tm in self.task_managers:
            tm.gdf = self.gdf

    @property
    def name(self):
        return self.info.name

    def rename(self, new_name: str):
        self.info.name = new_name
        return self

    def update_geofence(self, geometry: Polygon) -> gpd.GeoDataFrame:
        """
        Updatet de grens van het veld. 
        Verwacht een puur Shapely Polygon object vanuit de backend!
        """
        if not self.gdf.empty and 'name' in self.gdf.columns:
            mask = self.gdf['name'] == 'geofence'
        else:
            mask = pd.Series([False])

        if mask.any():
            self.gdf.loc[mask, 'geometry'] = geometry
        else:
            new_row = gpd.GeoDataFrame({
                'name': ['geofence'], 
                'type': ['polygon']
            }, geometry=[geometry], crs=self.gdf.crs if not self.gdf.empty else "EPSG:4326")
            self.gdf = pd.concat([self.gdf, new_row], ignore_index=True)
        
        self._sync_gdfs()
        return self.gdf

    def update_traject(self, geometry: LineString) -> gpd.GeoDataFrame:
        """Delegeert naar TrajectManager. Verwacht een pure LineString."""
        self.gdf = self.traject_manager.update_geometry(geometry)
        self._sync_gdfs()
        return self.gdf

    def add_new_task(self):
        base_name = 'Task'
        task_numbers = set()

        for tm in self.task_managers:
            if tm.name.startswith(base_name):
                suffix = tm.name[len(base_name):]
                if suffix.isdigit():
                    task_numbers.add(int(suffix))

        available_numbers = set(range(1, 100)) - task_numbers
        new_task_name = f"{base_name}{min(available_numbers)}"

        new_task_info = Task(name=new_task_name, type=HitchType.HITCH, hitch=HitchName.HITCH_FB)
        return self.add_task(new_task_info)

    def add_task(self, task_info: Task, geometry: Union[Polygon, MultiPoint] = None) -> TaskManager:
        tm = TaskManager(task_info=task_info, field_gdf=self.gdf)
        self.gdf = tm.update(geometry)
        
        self.task_managers.append(tm)
        self._sync_gdfs()
        return tm

    def update_task(self, task_name: str, geometry: Union[Polygon, MultiPoint] = None, task_info: Task = None) -> gpd.GeoDataFrame:
        tm = self.get_task(task_name)
        assert tm is not None, f"Task {task_name} does not exist."

        if task_info is not None:
            self.gdf = tm.update_info(task_info)
        if geometry is not None:
            self.gdf = tm.update(geometry)
            
        self._sync_gdfs()
        return self.gdf

    def remove_task(self, task_name: str) -> gpd.GeoDataFrame:
        tm = self.get_task(task_name)
        assert tm is not None, f"Task {task_name} does not exist."
        
        self.gdf = tm.delete() 
        self.task_managers.remove(tm)
        self._sync_gdfs()
        
        return self.gdf

    def get_task(self, task_name: str) -> Optional[TaskManager]:
        for tm in self.task_managers:
            if tm.name == task_name:
                return tm
        return None

    @property
    def context(self):
        task_dict = {tm.name: tm.context for tm in sorted(self.task_managers, key=lambda t: t.name)}
        
        geofence_geom = None
        traject_geom = None
        
        if not self.gdf.empty and 'name' in self.gdf.columns:
            gf_rows = self.gdf[self.gdf['name'] == 'geofence']
            if not gf_rows.empty:
                geofence_geom = gf_rows.geometry.iloc[0].__geo_interface__
                
            tr_rows = self.gdf[self.gdf['name'] == 'traject']
            if not tr_rows.empty:
                traject_geom = tr_rows.geometry.iloc[0].__geo_interface__

        return {
            'name': self.name,
            'geofence_geometry': geofence_geom,
            'traject_geometry': traject_geom,
            'tasks': task_dict
        }

    @property
    def json(self):
        ctx = self.context
        
        def wrap(geom):
            return {'empty': False, 'geojson': geom} if geom else {'empty': True}

        formatted_tasks = ctx.get('tasks', {})
        for t_name in formatted_tasks:
            t_geom = formatted_tasks[t_name].get('geometry')
            formatted_tasks[t_name]['geometry'] = wrap(t_geom)

        data = {
            'name': ctx['name'],
            'geofence': wrap(ctx['geofence_geometry']),
            'traject': wrap(ctx['traject_geometry']),
            'tasks': formatted_tasks
        }
        return json.dumps(data)