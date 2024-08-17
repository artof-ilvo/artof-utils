from artof_utils.redis import RedisServer
import artof_utils.paths as paths
import ipaddress
from os import getenv


# Redis server
def __is_numerical(input_str):
    try:
        # Try converting the string to a float
        float_value = float(input_str)
        return True
    except ValueError:
        # If ValueError is raised, it means the conversion failed
        return False


def __is_valid_ip(ip_str):
    try:
        ipaddress.ip_address(ip_str)
        return True
    except ValueError:
        return False


redis_server = RedisServer(ilvo_path=paths.ilvo_path,
                           host=getenv('REDIS_HOST') if getenv('REDIS_HOST') else '127.0.0.1',
                           port=int(getenv('REDIS_PORT'))
                           if getenv('REDIS_PORT') and __is_numerical(getenv('REDIS_PORT'))
                           else 6379)
