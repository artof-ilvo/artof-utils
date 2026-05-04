from typing import Optional

from pydantic import BaseModel, Field

class Traject(BaseModel):
    name: str = "traject"
    type: str = "LineString"
    raster_source: Optional[str] = Field(default="", description="Optionele bron van rasterdata voor dit traject")