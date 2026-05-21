from dataclasses import dataclass
from typing import Optional


@dataclass
class Device:
    device_type: str
    name: str
    site: str = ""
    ip: str = ""
    status: str = "UNKNOWN"
    owner: str = ""
    note: str = ""


@dataclass
class DeviceEvent:
    device_id: int
    event_type: str
    event_time: str
    recovery_time: Optional[str] = None
    downtime_minutes: Optional[int] = None
    source: str = ""
    raw_text: str = ""
