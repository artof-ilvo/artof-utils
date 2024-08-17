from artof_utils.schemas.settings import HitchType, HitchName
from artof_utils.implement import implement_manager


def get_hitch_choices():
    return [(hitch_name.value, hitch_name.value) for hitch_name in HitchName]


def get_type_choices():
    return [(hitch_type.value, hitch_type.value) for hitch_type in HitchType]


def get_implement_choices():
    return [('none', None)] + [(implement.name, implement.name) for implement in implement_manager.implements]
