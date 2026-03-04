from pydantic import BaseModel, field_validator
import re
from datetime import datetime
from typing import Optional

class Field(BaseModel):
    """
    Represents how a field is stored and validated. This class can be extended with additional attributes as needed
    """
    name: str
    # optional fields
    id: Optional[str] = None
    field_path: Optional[str] = None
    raster_path: Optional[str] = None
    created_at: Optional[datetime] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """
        Validates the field name to ensure it is not empty and does not contain illegal characters for file paths.
        """
        if not v or not v.strip():
            raise ValueError("field name cannot be empty or whitespace.")
        
        # Check op illegale tekens in mapnamen (Windows/Linux)
        if re.search(r'[\\/*?:"<>|]', v):
            raise ValueError(f"field name contains illegal file/path characters: {v}")
            
        return v.strip()

    @field_validator('created_at', mode='before')
    @classmethod
    def set_created_at(cls, v):
        """
        Ensures that the created_at field is set to the current datetime if it is not provided.
        """
        return v or datetime.now()

