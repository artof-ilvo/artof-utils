from pydantic import BaseModel, ConfigDict
from artof_utils.schemas.settings import HitchType, HitchName
from artof_utils.schemas.implement import Implement
from typing import Optional, Union
import numpy as np
import geopandas as gpd
from artof_utils.geojson import GeoJson, GeomType


class TaskInfo(BaseModel):
    name: str
    type: HitchType
    hitch: HitchName
    implement: str = ''


class Task(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    type: HitchType
    hitch: HitchName

    implement: Optional[Implement] = None
    geo_data: GeoJson

    def __init__(self, task_info: TaskInfo, geo_data: GeoJson):
        """
        Initializes the Task object.

        Args:
            task_path (str): The path to the task.
            task_info (TaskInfo): Information about the task.

        Returns:
            None
        """
        implement_ = Implement.load(task_info.implement) if task_info.implement else None

        super().__init__(name=task_info.name,
                         type=task_info.type,
                         hitch=task_info.hitch,
                         implement=implement_,
                         geo_data=geo_data)

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __lt__(self, other):
        return self.name < other.name

    def __gt__(self, other):
        return self.name > other.name

    def delete(self):
        self.geo_data.delete(self.name)

    def save(self):
        self.geo_data.save()

    def update(self, geometries: Union[list, np.array, gpd.GeoDataFrame], epsg: int = 0):
        properties = {
            'hitch_type': self.type.value if hasattr(self.type, 'value') else self.type,
            'hitch_name': self.hitch.value if hasattr(self.hitch, 'value') else self.hitch,
            'implement': self.implement.name if self.implement else ''
        }

        if isinstance(geometries, gpd.GeoDataFrame):
            for k, v in properties.items():
                geometries[k] = v
            self.geo_data.update(geometries, name=self.name, type="task")
        else:
            if self.type in [HitchType.HITCH, HitchType.CONTINUOUS, HitchType.CARDAN]:
                geom_type = GeomType.POLYGON
            else:
                geom_type = GeomType.POINT

            self.geo_data.update(
                geometries=geometries, 
                name=self.name, 
                type="task", 
                properties=properties, 
                epsg=epsg
            )

    def update_info(self, task_info: TaskInfo):
        self.type = task_info.type
        self.hitch = task_info.hitch
        self.implement = Implement.load(task_info.implement) if task_info.implement else None
        
        existing_row = self.geo_data.gdf[self.geo_data.gdf['name'] == self.name]
        existing_geom = existing_row.geometry.tolist() if not existing_row.empty else None
        
        self.update(geometries=existing_geom)

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
            'geometry': self.geo_data.context
        }
