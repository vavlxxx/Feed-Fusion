from datetime import datetime
import json
from pydantic import BaseModel, ConfigDict


class BaseDTO(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={datetime: lambda v: v.isoformat()},
        strict=True,
        str_min_length=1,
    )


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)
