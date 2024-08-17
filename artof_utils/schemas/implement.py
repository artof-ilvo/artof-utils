import json
from typing import Optional
from pydantic import BaseModel
from artof_utils.schemas.settings import Transform, HitchType
import artof_utils.paths as paths
from os import path


class Section(BaseModel):
    id: str = ""
    width: float = 0.0
    up: float = 0.03
    down: float = 0.03
    link_length: Optional[float] = None
    repeats: Optional[int] = None
    offset: Optional[float] = None
    transform: Transform


class Implement(BaseModel):
    name: str
    on_taskmap: Optional[bool] = True
    types: list[HitchType] = []
    sections: list[Section] = []

    @staticmethod
    def load(name: str):
        implement_file_path = path.join(paths.implements, '%s.json' % name)
        if path.exists(implement_file_path):
            with open(implement_file_path, 'r') as json_file:
                j = json.load(json_file)
                return Implement(**j)
        else:
            return Implement(name=name)

    @property
    def context(self):
        data = self.model_dump(exclude_none=True)
        data['types'] = [t.value for t in self.types] if self.types else []
        return data
