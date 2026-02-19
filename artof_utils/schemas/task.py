from pydantic import BaseModel, ConfigDict
from artof_utils.schemas.settings import HitchType, HitchName
from artof_utils.schemas.implement import Implement
from typing import Optional, Union
import numpy as np
import geopandas as gpd
from artof_utils.geojson import GeoJson, GeomType
from artof_utils.helpers.raster import Raster as rstr


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

    # ... (Bestaande imports) ...
    
    def update(self, geometries: Union[list, np.array, gpd.GeoDataFrame], epsg: int = 0):
        """
        Update de taak.
        """
        # 1. Metadata voorbereiden
        properties = {
            'hitch_type': self.type.value if hasattr(self.type, 'value') else self.type,
            'hitch_name': self.hitch.value if hasattr(self.hitch, 'value') else self.hitch,
            'implement': self.implement.name if self.implement else ''
        }

        if self.type in [HitchType.CONTINUOUS, HitchType.HITCH]:
            type = GeomType.POLYGON
        # Als het gaat om punt-acties (onkruid detectie/stappen)
        else:
            type = GeomType.MULTIPOINT

        # 2. Settings ophalen
        from artof_utils.robot import robot_manager
        try:
            cfg = robot_manager.platform_settings.robot
            resolution = getattr(cfg, 'raster', {}).get('default_resolution', 0.05)
        except Exception:
            resolution = 0.05

        # 3. SAVE (Geen conversie meer hier!)
        # We geven gewoon de ruwe 'geometries' door.
        self.geo_data.save_as_raster(
            name=self.name,
            data=geometries,  # <--- Ruwe data gaat erin
            resolution=resolution,
            properties=properties,
            type=type,
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
