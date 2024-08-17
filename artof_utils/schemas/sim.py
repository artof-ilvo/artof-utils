from pydantic import BaseModel


class SimStatus(BaseModel):
    active_sim: bool
    sim_active_auto: bool


class KeyboardCommand(BaseModel):
    vel_fwd: float
    omega: float


class SimPosition(BaseModel):
    x: float
    y: float
    yaw: float


class SpeedFactor(BaseModel):
    factor: float
