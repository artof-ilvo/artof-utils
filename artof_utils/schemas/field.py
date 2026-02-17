import json
from os import listdir
import re
import numpy as np
from shutil import copytree, rmtree, move
from os import path, makedirs
from pydantic import BaseModel, ConfigDict
from typing import Any, Union
import geopandas as gpd
from artof_utils.geojson import GeoJson, GeomType

from artof_utils.schemas.task import Task
from artof_utils.schemas.traject import Traject
from artof_utils.schemas.task import TaskInfo, HitchType, HitchName
import artof_utils.paths as paths
from artof_utils.redis_instance import redis_server

import os

def get_field_names() -> list:
    if not path.exists(paths.fields):
        os.makedirs(paths.fields, exist_ok=True)
        return []
    field_names_ = [
        f for f in os.listdir(paths.fields) 
        if os.path.isdir(path.join(paths.fields, f)) and not f.startswith('.')
    ]
    field_names_.sort()

    return field_names_


def get_current_field_name():
    field_name = redis_server.get_value('pc.field.name')
    
    available_fields = get_field_names()

    if not field_name or field_name not in available_fields:
        if len(available_fields) > 0:
            field_name = available_fields[0]
            redis_server.set_value('pc.field.name', field_name)
        else:
            return ""

    return field_name


class Field(BaseModel):
    pass

class Fields(BaseModel):
    current_field: str = ""
    fields: list[str] = []

    def __init__(self):
        """
        The calculations are performed on the dictionary objects whereas it is not necessary to interpret the Field
        :return: json object listing the fields and there distance to current_state in [m]
        """
        super().__init__(current_field=get_current_field_name(), fields=get_field_names())

    def refresh(self):
        self.fields = get_field_names()

    def select_field(self, field_name):
        assert field_name in self.fields, f"Field {field_name} does not exist."

        if field_name != self.current_field:
            redis_server.set_n_values({'pc.field.name': field_name, 'pc.field.updated': True})

    def delete_field(self, field_name):
        assert field_name != self.current_field, f"Field {field_name} is currently active."

        if self.exists(field_name):
            field_path = path.join(paths.fields, field_name)
            rmtree(field_path, ignore_errors=True)
            self.refresh()


    def duplicate_field(self, field_name) -> Field:
        assert field_name in self.fields, f"Field {field_name} does not exist."

        field_path = path.join(str(paths.fields), field_name)
        new_field_name = f"{field_name}_copy"
        new_field_path = path.join(paths.base, "field", new_field_name)
        copytree(str(field_path), str(new_field_path), dirs_exist_ok=True)

        new_field = Field(new_field_name)

        new_field.geo_data.gdf['field_name'] = new_field_name 
        new_field.geo_data.save()

        self.refresh()

        return new_field

    def exists(self, field_name):
        return field_name in self.fields

    @property
    def context(self):
        return self.model_dump()


class Field(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    field_path: str
    raster_path: str
    geo_data: GeoJson
    traject: Traject
    tasks: list[Task] = []

    def __init__(self, name):
        field_path_ = path.join(str(paths.fields), name)
        raster_path_ = path.join(field_path_, "rasters")
        makedirs(raster_path_, exist_ok=True)

        geo_data = GeoJson(field_path_)
        traject_ = Traject(geo_data)
        tasks_ = []
        if geo_data.gdf is not None and not geo_data.gdf.empty:
            task_rows = geo_data.gdf[geo_data.gdf['type'] == 'task']
            
            for _, row in task_rows.iterrows():
                t_info = TaskInfo(
                    name=row['name'],
                    type=row.get('hitch_type', HitchType.HITCH),
                    hitch=row.get('hitch_name', HitchName.HITCH_FB),
                    implement=row.get('implement', '')
                )
                tasks_.append(Task(task_info=t_info, geo_data=geo_data))

        # Call super class
        super().__init__(
            name=name,
            field_path=field_path_,
            raster_path=raster_path_,
            geo_data=geo_data,
            traject=traject_,
            tasks=tasks_
        )

    def rename(self, new_name):
        assert not Fields().exists(new_name), f"Field {new_name} already exists."
        
        old_path = self.field_path
        new_path = path.join(paths.fields, new_name)
        
        self.name = new_name
        
        move(old_path, str(new_path))
        self.field_path = str(new_path)

        self.geo_data.folder_path = str(new_path)
        self.geo_data.file_path = path.join(str(new_path), f"{self.geo_data.filename}.geojson")
        
        return self
    
    @property
    def context(self):
        traject_geometry_ = self.traject.context
        geofence_geometry_ = self.geo_data.get_layer_context('geofence')
        task_geometries_ = [task.context for task in self.tasks]

        # j_traject = redis_server.get_json_value('traject')
        # if j_traject:
        #     wgs84_crs = 'EPSG:4326'  # WGS 84
        #     input_crs = 'EPSG:%d' % self.shp_traject.gdf.crs.to_epsg()
        #
        #     traject_skeleton_xy = [[point['x'], point['y']] for point in j_traject['skeleton']]
        #     traject_skeleton_latlng = shp.transform_crs(input_crs, wgs84_crs, traject_skeleton_xy)
        #
        #     traject_corners_xy = [[point['x'], point['y']] for point in j_traject['corners']]
        #     traject_corners_latlng = shp.transform_crs(input_crs, wgs84_crs, traject_corners_xy)
        #
        #     traject_geometry_['skeleton'] = {'xy': traject_skeleton_xy, 'latlng': traject_skeleton_latlng}
        #     traject_geometry_['corners'] = {'xy': traject_corners_xy, 'latlng': traject_corners_latlng}

        task_dict = dict()
        for task in sorted(self.tasks):
            task_dict[task.name] = task.context

        field_data = {
            'name': self.name,
            'traject_geometry': traject_geometry_,
            'geofence_geometry': geofence_geometry_,
            'task_geometries': task_geometries_,
            'field_json': json.dumps({'name': self.name, 'traject': traject_geometry_,
                                      'geofence': geofence_geometry_, 'tasks': task_dict})
        }

        return field_data

    #def update_info(self):
     #   self.info.tasks = [task.task_info for task in self.tasks]
#
 #       with open(self.info_file_path, 'w') as json_file:
  #          json.dump(self.info.context, json_file, indent=4)

    def update_geofence(self, geometries: Union[list, np.array, gpd.GeoDataFrame] | None = None, epsg: int = 0):
        self.geo_data.update(geometries=geometries, type=GeomType.POLYGON, name="geofence", epsg=epsg)

    def update_traject(self, geometries, epsg: int = 0):
        self.traject.update(geometries, epsg=epsg)

    def update_task(self, task_name, geometries: Union[list, np.array, gpd.GeoDataFrame] | None = None,
                    task_info: TaskInfo | None = None, epsg: int = 0):
        task = self.get_task(task_name)
        assert task is not None, f"Task {task_name} does not exist."

        if task_info is not None:
            task.update_info(task_info)

        if geometries is not None:
            task.update(geometries, epsg=epsg)

    def add_new_task(self):
        base_name = 'Task'
        task_numbers = set()

        for task in self.tasks:
            if task.name.startswith(base_name):
                suffix = task.name[len(base_name):]
                
                if suffix.isdigit():
                    task_numbers.add(int(suffix))

        available_numbers = set(range(1, 100)) - task_numbers
        new_task_name = f"{base_name}{min(available_numbers)}"

        new_task_info = TaskInfo(name=new_task_name, type=HitchType.HITCH, hitch=HitchName.HITCH_FB)
        self.add_task(new_task_info)

    def add_task(self, task_info: TaskInfo, geometries=None):
        new_task = Task(task_info=task_info, geo_data=self.geo_data)
        new_task.update(geometries=geometries)
        self.tasks.append(new_task)
        return new_task
    
    def remove_task(self, task_name):
        task = self.get_task(task_name)
        assert task is not None, f"Task {task_name} does not exist."
        task.delete()  # Remove geojson from storage
        self.tasks.remove(task)  # Remove task from list

    def get_task(self, task_name):
        for task in self.tasks:
            if task.name == task_name:
                return task
        return None
