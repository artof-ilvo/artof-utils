from pydantic import BaseModel, Field
from typing import Optional
from artof_utils.schemas.settings import HitchType, HitchName

class Task(BaseModel):
    """
    Puur Pydantic data-schema voor een Taak.
    """
    name: str = Field(..., description="Unieke naam van de taak")
    type: HitchType = Field(default=HitchType.HITCH)
    hitch: HitchName = Field(default=HitchName.HITCH_FB)
    implement: str = Field(default="", description="Naam van het gekoppelde werktuig")
