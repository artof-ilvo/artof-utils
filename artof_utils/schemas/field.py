import json
from os import listdir
import re
import numpy as np
from shutil import copytree, rmtree, move
from os import path, makedirs
from pydantic import BaseModel, ConfigDict
from typing import Any, Union
import geopandas as gpd

from artof_utils.schemas.task import Task
from artof_utils.schemas.task import TaskInfo, HitchType, HitchName
import artof_utils.paths as paths
from artof_utils.redis_instance import redis_server
from artof_utils.shapefile import Shapefile, GeomType
from artof_utils.helpers import shape as shp


def get_field_names() -> list:
    assert path.exists(paths.fields), 'Field path %s does not exist.' % paths.fields
    field_names_ = listdir(paths.fields)
    assert len(field_names_) > 0, 'The folder %s does not contain any fields' % paths.fields

    return field_names_


def get_current_field_name():
    # Assert the active_field exists
    field_name = redis_server.get_value('pc.field.name')

    if not field_name:
        field_name = get_field_names()[0]
        redis_server.set_value('pc.field.name', field_name)

    return field_name


class Field(BaseModel):
    pass


class FieldInfo(BaseModel):
    name: str
    tasks: list[TaskInfo]

    @property
    def context(self):
        return self.model_dump(exclude_none=True, exclude_defaults=True)


class Fields(BaseModel):
    current_field: str = ""
    fields: list[str] = []

    def __init__(self):
        """
        The calculations are performed on the dictionary objects whereas it is not necessary to interpret the Field
        :return: json object listing the fields and there distance to current_state in [m]
        """
        super().__init__(current_field=get_current_field_name(), fields=get_field_names())

    def select_field(self, field_name):
        assert field_name in self.fields, f"Field {field_name} does not exist."

        if field_name != self.current_field:
            redis_server.set_n_values({'pc.field.name': field_name, 'pc.field.updated': True})

    def delete_field(self, field_name):
        assert field_name != self.current_field, f"Field {field_name} is currently active."

        if self.exists(field_name):
            field_path = path.join(paths.base, "field", field_name)
            rmtree(field_path, ignore_errors=True)

    def duplicate_field(self, field_name) -> Field:
        assert field_name in self.fields, f"Field {field_name} does not exist."

        field_path = path.join(paths.base, "field", field_name)
        new_field_name = f"{field_name}_copy"
        new_field_path = path.join(paths.base, "field", new_field_name)
        copytree(str(field_path), str(new_field_path), dirs_exist_ok=True)

        return Field(new_field_name)

    def exists(self, field_name):
        return field_name in self.fields

    @property
    def context(self):
        return self.model_dump()


class Field(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    field_path: str
    geofence_path: str
    traject_path: str
    tasks_path: str
    info_file_path: str

    info: FieldInfo

    shp_traject: Shapefile
    shp_geofence: Shapefile

    tasks: list[Task] = []

    def __init__(self, name):
        field_path_ = path.join(str(paths.fields), name)
        geofence_path_ = path.join(str(field_path_), "geofence")
        traject_path_ = path.join(str(field_path_), "traject")
        tasks_path_ = path.join(str(field_path_), "tasks")
        info_file_path_ = path.join(str(field_path_), "info.json")

        # Process info
        update_info = False
        if path.exists(info_file_path_):
            with open(info_file_path_, 'r') as json_file:
                j = json.load(json_file)
                field_info_: FieldInfo = FieldInfo.model_validate(j)
                # overwrite name from json if name is not equal
                if field_info_.name != name:
                    field_info_.name = name
                    update_info = True
        else:
            field_info_ = FieldInfo(name=name, tasks=[])
            update_info = True

        # Process tasks
        makedirs(tasks_path_, exist_ok=True)
        tasks_: list[Task] = []
        for task_info in field_info_.tasks:
            task_path = path.join(tasks_path_, task_info.name)
            tasks_.append(Task(task_path, task_info))

        if update_info:
            with open(info_file_path_, 'w') as json_file:
                json.dump(field_info_.context, json_file, indent=4)

        # Call super class
        super().__init__(name=name,
                         field_path=field_path_,
                         geofence_path=geofence_path_,
                         traject_path=traject_path_,
                         tasks_path=tasks_path_,
                         info_file_path=info_file_path_,
                         info=field_info_,
                         shp_traject=Shapefile(traject_path_),
                         shp_geofence=Shapefile(geofence_path_),
                         tasks=tasks_
                         )

    def rename(self, new_name):
        # check if new_name exists
        assert not Fields().exists(new_name), f"Field {new_name} already exists."

        # update info
        self.info.name = new_name
        with open(self.info_file_path, 'w') as json_file:
            json.dump(self.info.context, json_file, indent=4)
        # move files
        new_path = path.join(paths.fields, new_name)
        move(self.field_path, str(new_path))

        return Field(new_name)

    @property
    def context(self):
        traject_geometry_ = self.shp_traject.context
        geofence_geometry_ = self.shp_geofence.context
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
            'traject_geometry': traject_geometry_,
            'geofence_geometry': geofence_geometry_,
            'task_geometries': task_geometries_,
            'field_json': json.dumps({'name': self.name, 'traject': traject_geometry_,
                                      'geofence': geofence_geometry_, 'tasks': task_dict})
        }

        return field_data

    def update_info(self):
        self.info.tasks = [task.task_info for task in self.tasks]

        with open(self.info_file_path, 'w') as json_file:
            json.dump(self.info.context, json_file, indent=4)

    def update_geofence(self, geometries: Union[list, np.array, gpd.GeoDataFrame] | None = None, epsg: int = 0):
        self.shp_geofence.update(geometries, GeomType.POLYGON, epsg=epsg)

    def update_traject(self, geometries: Union[list, np.array, gpd.GeoDataFrame] | None = None, epsg: int = 0):
        self.shp_traject.update(geometries, GeomType.LINESTRING, epsg=epsg)

    def update_task(self, task_name, geometries: Union[list, np.array, gpd.GeoDataFrame] | None = None,
                    task_info: TaskInfo | None = None, epsg: int = 0):
        task = self.get_task(task_name)
        assert task is not None, f"Task {task_name} does not exist."

        if task_info is not None:
            task.update_info(task_info)
            self.update_info()

        if geometries is not None:
            task.update(geometries, epsg=epsg)

    def add_new_task(self):
        # Extract basename
        regex_pattern = r'\d+'
        base_names = set()
        task_numbers = set()
        for task in self.tasks:
            name = task.name
            result_name = re.sub(regex_pattern, '', name)
            result_number = re.search(regex_pattern, name)
            base_names.add(result_name)
            task_numbers.add(int(result_number.group()))

        assert len(base_names) <= 1, "All tasks must have the same basename"
        if len(base_names) == 0:
            base_name = 'Task'
        else:
            base_name = base_names.pop()
        task_numbers = set(list(range(1, 100))) - set(task_numbers)

        # Create new task
        new_task_name = base_name + str(min(task_numbers))

        # Add new task
        new_task_info = TaskInfo(name=new_task_name, type=HitchType.HITCH, hitch=HitchName.HITCH_FB)
        self.add_task(new_task_info)

    def add_task(self, task_info: TaskInfo, geometries: Union[list, np.array, gpd.GeoDataFrame] | None = None):
        task = Task(task_path=path.join(self.tasks_path, task_info.name), task_info=task_info)
        if geometries is not None:
            task.update(geometries)
        self.tasks.append(task)  # Add task to list
        self.update_info()

    def remove_task(self, task_name):
        task = self.get_task(task_name)
        assert task is not None, f"Task {task_name} does not exist."
        task.delete()  # Remove shapefiles from storage
        self.tasks.remove(task)  # Remove task from list
        self.update_info()

    def get_task(self, task_name):
        for task in self.tasks:
            if task.name == task_name:
                return task
        return None
