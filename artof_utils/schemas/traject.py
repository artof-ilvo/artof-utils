from pydantic import BaseModel

class Traject(BaseModel):
    name: str = "traject"
    type: str = "LineString"