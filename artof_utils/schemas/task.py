from pydantic import BaseModel, Field
from typing import Optional
from artof_utils.schemas.settings import HitchType, HitchName

class Task(BaseModel):
    """
    Puur Pydantic data-schema voor een Taak.
    """
    name: str = Field(..., description="Unieke naam van de taak")
    type: str = Field(default="task", description="Type van de geometrie, standaard 'task'")
    hitch_type: HitchType = Field(default=HitchType.HITCH)
    hitch_name: HitchName = Field(default=HitchName.HITCH_FB)
    implement: str = Field(default="", description="Naam van het gekoppelde werktuig")
    raster_source: Optional[str] = Field(default="", description="Optionele bron van rasterdata voor deze taak")
    overlay_source: Optional[str] = Field(default="", description="Optionele bron van overlay data voor deze taak")
    bounds: Optional[tuple] = Field(default=None, description="Optionele bounds van de rasterdata in (minx, miny, maxx, maxy)")
