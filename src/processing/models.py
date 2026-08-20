from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ArrivalEvent(BaseModel):
    vehicle_id: Optional[str] = None
    line_id: str
    line_name: str
    station_id: str
    station_name: str
    destination_name: Optional[str] = None
    direction: Optional[str] = None

    time_to_station: int = Field(ge=0)

    expected_arrival: Optional[datetime] = None
    timestamp: Optional[datetime] = None

    mode_name: Optional[str] = None
    platform_name: Optional[str] = None