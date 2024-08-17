from pydantic import BaseModel, ConfigDict
from artof_utils.schemas.settings import HitchType, HitchName
from artof_utils.shapefile import Shapefile, GeomType
from artof_utils.schemas.implement import Implement
from typing import Optional, Union
from os import path, makedirs, removedirs
import numpy as np
import geopandas as gpd
from shutil import rmtree


class TaskInfo(BaseModel):
    name: str
    type: HitchType
    hitch: HitchName
    implement: str = ''


class Task(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    task_path: str
    type: HitchType
    hitch: HitchName

    implement: Optional[Implement] = None
    shp_task: Shapefile

    def __init__(self, task_path: str, task_info: TaskInfo):
        """
        Initializes the Task object.

        Args:
            task_path (str): The path to the task.
            task_info (TaskInfo): Information about the task.

        Returns:
            None
        """
        # Create the path if it does not exist
        if not path.exists(task_path):
            makedirs(task_path, exist_ok=True)

        name_ = task_info.name
        shp_task_ = Shapefile(task_path)
        implement_ = Implement.load(task_info.implement) if task_info.implement else None

        super().__init__(name=name_,
                         task_path=task_path,
                         type=task_info.type,
                         hitch=task_info.hitch,
                         implement=implement_,
                         shp_task=shp_task_)

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __lt__(self, other):
        return self.name < other.name

    def __gt__(self, other):
        return self.name > other.name

    def delete(self):
        rmtree(self.task_path)

    def save(self):
        makedirs(self.task_path, exist_ok=True)
        self.shp_task.save()

    def update(self, geometries: Union[list, np.array, gpd.GeoDataFrame], epsg: int = 0):
        if isinstance(geometries, gpd.GeoDataFrame):
            self.shp_task.update(geometries)
        else:
            if self.type in [HitchType.HITCH, HitchType.CONTINUOUS, HitchType.CARDAN]:
                geom_type = GeomType.POLYGON
            elif self.type in [HitchType.DISCRETE, HitchType.INTERMITTENT]:
                geom_type = GeomType.POINT
            else:
                geom_type = GeomType.POLYGON

            self.shp_task.update(geometries, geom_type, epsg=epsg)

    def update_info(self, task_info: TaskInfo):
        self.type = task_info.type
        self.hitch = task_info.hitch
        self.implement = Implement.load(task_info.implement) if task_info.implement else None

    @property
    def task_info(self):
        return TaskInfo(name=self.name,
                        type=self.type,
                        hitch=self.hitch,
                        implement=self.implement.name if self.implement else '')

    @property
    def context(self):
        return {
            'name': self.name,
            'type': self.type.value,
            'hitch': self.hitch.value,
            'implement': self.implement.name if self.implement else '',
            'geometry': self.shp_task.context
        }
