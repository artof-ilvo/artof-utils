

# Gps
def parse_gps_fix_number(gps_fix_number):
    """
    Parse GPS fix number
    :param gps_fix_number: GPS fix number
    :return: GPS fix number description
    """
    if gps_fix_number == 0:
        return 'Not valid'
    elif gps_fix_number == 1:
        return 'GPS Fix'
    elif gps_fix_number == 2:
        return 'Differential GPS'
    elif gps_fix_number == 3:
        return 'Not applicable'
    elif gps_fix_number == 4:
        return 'RTK Fix'
    elif gps_fix_number == 5:
        return 'RTK Float'
    else:
        return 'Not valid'
