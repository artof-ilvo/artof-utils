from enum import Enum

from pydantic import BaseModel, model_validator
from typing import Optional, Any
import artof_utils.paths as paths
import json


class RobotAutoMode(str, Enum):
    NORMAL = "normal"
    FULL = "auto_full"
    STEER = "auto_steer"
    THROTTLE = "auto_throttle"
    PLAYBACK = "teachandplay_play"
    END = "end_reached"


class DirNames(str, Enum):
    TRAJECT = "traject"
    GEOFENCE = "geofence"
    TEACH_AND_PLAY = "teach_and_play"
    TASK1 = "Task1"
    TASK2 = "Task2"
    TASK3 = "Task3"
    TASK4 = "Task4"
    TASK5 = "Task5"


class HitchType(str, Enum):
    HITCH = "hitch"
    CONTINUOUS = "continuous"
    DISCRETE = "discrete"
    CARDAN = "cardan"
    INTERMITTENT = "intermittent"


class HitchName(str, Enum):
    HITCH_FF = "FF"
    HITCH_FB = "FB"
    HITCH_RB = "RB"


class Transform(BaseModel):
    T: list[float] = [0.0, 0.0, 0.0]
    R: list[float] = [0.0, 0.0, 0.0]


class Hitch(BaseModel):
    id: int = 0.0
    name: HitchName = HitchName.HITCH_FB
    min: float = 0.0
    max: float = 0.0
    types: list[HitchType] = []
    transform: Transform
    float: bool = False
    # Redis variables
    setpoint: int = 0
    activate: bool = False
    start_discr_impl: bool = False
    activate_cont_impl: bool = False
    activate_cardan: bool = False
    activate_section: list[bool] = [False] * 32


class Robot(BaseModel):
    width: float = 1.0
    length: float = 1.0
    wheel_diameter: float = 0.5
    transform: Transform
    transform_center: Transform
    transform_head: Transform

    @model_validator(mode='before')
    @classmethod
    def set_transform_center(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if 'transform_center' not in data:
                data['transform_center'] = data['transform']
            if 'transform_head' not in data:
                data['transform_head'] = data['transform']
        return data


class AutoVelocity(BaseModel):
    min: float = 0.0
    max: float = 1.0


class NavMode(BaseModel):
    id: int
    name: str


class AutoMode(BaseModel):
    id: int
    name: str


class Gps(BaseModel):
    device: str
    utm_zone: int
    udp_port: Optional[int] = None
    ip: Optional[str] = None
    usb_port: Optional[str]
    ntrip_server: Optional[str]
    ntrip_mountpoint: Optional[str]
    ntrip_uname: Optional[str]
    ntrip_pwd: Optional[str]
    transform: Transform


class PlatformSettings(BaseModel):
    name: str
    robot: Robot
    auto_velocity: AutoVelocity
    nav_modes: list[NavMode]
    auto_modes: list[AutoMode]
    hitches: list[Hitch]
    gps: Gps

    @property
    def context(self):
        return self.model_dump()


def load_settings() -> PlatformSettings:
    with open(paths.platform_settings, 'r') as f:
        settings = PlatformSettings.model_validate(json.load(f))
    return settings
