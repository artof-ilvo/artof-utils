from pydantic import BaseModel
from typing import Optional
from artof_utils.schemas.settings import Hitch
from artof_utils.redis_instance import redis_server
from copy import deepcopy


class Hitches(BaseModel):
    hitches: Optional[list[Hitch]] = []

    redis_variables: list[str]

    def __init__(self):
        super().__init__(redis_variables=[])

    def add_hitches(self, hitches: list[Hitch]):
        self.hitches = deepcopy(hitches)

        # Add hitch redis variables
        for hitch in self.hitches:
            hitch_name = 'plc.control.hitch_' + hitch.name.lower()
            self.redis_variables.append(hitch_name + '.activate')
            self.redis_variables.append(hitch_name + '.active_discrete')
            self.redis_variables.append(hitch_name + '.active_continuous')
            self.redis_variables.append(hitch_name + '.active_cardan')
            self.redis_variables.append(hitch_name + '.setpoint')
            for i in range(32):
                self.redis_variables.append(hitch_name + '.activate_sections.%d' % i)

        self.update()

    def update(self):
        d = redis_server.get_n_values(self.redis_variables)

        # Update hitches
        for hitch in self.hitches:
            hitch_name = 'plc.control.hitch_' + hitch.name.lower()
            hitch.activate = d[hitch_name + '.activate']
            hitch.start_discr_impl = d[hitch_name + '.active_discrete']
            hitch.activate_cont_impl = d[hitch_name + '.active_continuous']
            hitch.activate_cardan = d[hitch_name + '.active_cardan']
            hitch.setpoint = d[hitch_name + '.setpoint']
            hitch.float = hitch.setpoint == 99
            for i in range(32):
                variable_name = hitch_name + '.activate_sections.%d' % i
                hitch.activate_section[i] = d[variable_name]

    @staticmethod
    def change(hitch_setpoints: dict):
        d = {}
        for name, setpoint in hitch_setpoints.items():
            hitch_name = 'plc.control.hitch_' + name.lower()
            d[hitch_name + '.setpoint'] = setpoint
        redis_server.set_n_values(d)

    @property
    def context(self):
        return self.model_dump(exclude={'redis_variables'})
