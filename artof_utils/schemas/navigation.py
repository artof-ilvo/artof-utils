from pydantic import BaseModel
from typing import Optional
from artof_utils.redis_instance import redis_server


class Navigation(BaseModel):
    navigation_mode: int
    non_operational_velocity: float
    operational_velocity: float
    carrot_distance: Optional[float]
    weight_factor: Optional[float] = 0.0
    kp_steady_state: Optional[float] = 0.0
    ki_steady_state: Optional[float] = 0.0
    kd_steady_state: Optional[float] = 0.0
    kp_rough: Optional[float] = 0.0
    ki_rough: Optional[float] = 0.0
    kd_rough: Optional[float] = 0.0

    redis_variables: list[str]

    def __init__(self):
        redis_variables_ = [
            "pc.navigation.mode",
            "pc.navigation.non_operational_velocity",
            "pc.navigation.operational_velocity",
            "pc.purepursuit.weight_factor",
            "pc.purepursuit.carrot_distance",
            "pc.pid_steady_state.p",
            "pc.pid_steady_state.i",
            "pc.pid_steady_state.d",
            "pc.pid_rough.p",
            "pc.pid_rough.i",
            "pc.pid_rough.d"
        ]
        d = redis_server.get_n_values(redis_variables_)

        super().__init__(navigation_mode=d['pc.navigation.mode'],
                         non_operational_velocity=d['pc.navigation.non_operational_velocity'],
                         operational_velocity=d['pc.navigation.operational_velocity'],
                         weight_factor=d['pc.purepursuit.weight_factor'],
                         carrot_distance=d['pc.purepursuit.carrot_distance'],
                         kp_steady_state=d['pc.pid_steady_state.p'],
                         ki_steady_state=d['pc.pid_steady_state.i'],
                         kd_steady_state=d['pc.pid_steady_state.d'],
                         kp_rough=d['pc.pid_rough.p'],
                         ki_rough=d['pc.pid_rough.i'],
                         kd_rough=d['pc.pid_rough.d'],
                         redis_variables=redis_variables_)

    def update(self):
        d = redis_server.get_n_values(self.redis_variables)
        self.navigation_mode = d['pc.navigation.mode']
        self.non_operational_velocity = d['pc.navigation.non_operational_velocity']
        self.operational_velocity = d['pc.navigation.operational_velocity']
        self.weight_factor = d['pc.purepursuit.weight_factor']
        self.kp_steady_state = d['pc.pid_steady_state.p']
        self.ki_steady_state = d['pc.pid_steady_state.i']
        self.kd_steady_state = d['pc.pid_steady_state.d']
        self.kp_rough = d['pc.pid_rough.p']
        self.ki_rough = d['pc.pid_rough.i']
        self.kd_rough = d['pc.pid_rough.d']
        self.carrot_distance = d['pc.purepursuit.carrot_distance']

    @staticmethod
    def change(navigation_mode: int, non_operational_velocity: float, operational_velocity: float,
               carrot_distance: float, weight_factor: float,
               kp_steady_state: float, ki_steady_state: float, kd_steady_state: float,
               kp_rough: float, ki_rough: float, kd_rough: float):
        d = {
            'pc.navigation.mode': navigation_mode,
            'pc.navigation.non_operational_velocity': non_operational_velocity,
            'pc.navigation.operational_velocity': operational_velocity,
            'pc.purepursuit.weight_factor': weight_factor,
            'pc.pid_steady_state.p': kp_steady_state,
            'pc.pid_steady_state.i': ki_steady_state,
            'pc.pid_steady_state.d': kd_steady_state,
            'pc.pid_rough.p': kp_rough,
            'pc.pid_rough.i': ki_rough,
            'pc.pid_rough.d': kd_rough,
            'pc.purepursuit.carrot_distance': carrot_distance
        }
        redis_server.set_n_values(d)

    @property
    def context(self):
        return self.model_dump(exclude={'redis_variables'})
