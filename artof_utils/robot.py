import time

from artof_utils.singleton import Singleton
from artof_utils.schemas.settings import load_settings
from artof_utils.schemas.field import Field, get_current_field_name
from artof_utils.schemas.hitches import Hitches
from artof_utils.schemas.navigation import Navigation
from artof_utils.schemas.state import State
from artof_utils.helpers import hardware as hw
from artof_utils.helpers import shape as shp
from artof_utils.helpers import polygon
from artof_utils.schemas.settings import AutoMode
from artof_utils.redis_instance import redis_server
from shapely.geometry import Point


# Robot Manager
class RobotManager(metaclass=Singleton):
    """
    A singleton class responsible for managing the robot's settings, field information,
    navigation, and interaction with external resources like redis_server. This ensures a single
    instance can manage and maintain the state and behavior of the robotic platform.
    """

    def __init__(self):
        """
        Initializes the RobotManager instance by loading platform settings and field
        information, setting up hitches and navigation objects, and preparing state
        and voltage variables.
        """
        self.platform_settings = None
        self.field = None

        # Load settings and field from configuration files
        self.load_settings()
        self.load_field()

        # Initialize Hitches and Navigation objects
        self.hitches = Hitches()
        self.navigation = Navigation()

        # Configure platform hitches based on loaded settings
        if self.platform_settings:
            self.hitches.add_hitches(self.platform_settings.hitches)

        # Retrieve robot state and voltage information from Redis
        all_keys = redis_server.variables.keys()
        self.robot_state_vars = [key for key in all_keys if key.startswith('plc.monitor.state.')]

    def load_settings(self):
        """Loads platform settings from a JSON file specified in the paths configuration."""
        print("Load settings")
        self.platform_settings = load_settings()

    def load_field(self):
        """Loads the current field configuration based on the field name."""
        print("Load Field")
        self.field = Field(get_current_field_name())

    # Getter and setters
    @staticmethod
    def get_navigation_modes():
        return [(mode.id, mode.name) for mode in robot_manager.platform_settings.nav_modes]

    def get_navigation_states(self):
        """
        Retrieves a list of available navigation states for the robot, including
        any custom auto modes defined in the platform settings.

        Returns:
            list: A list of navigation state names.
        """
        auto_modes_settings = [AutoMode.model_validate({'name': 'normal', 'id': 0})] + self.platform_settings.auto_modes
        state_names = [auto_mode_setting.name for auto_mode_setting in auto_modes_settings]
        return state_names

    def get_navigation_state(self):
        state_vars = redis_server.get_n_values(self.robot_state_vars)
        active_states = [k.replace('plc.monitor.state.', '') for k, v in state_vars.items() if v]
        current_state = active_states[0] if len(active_states) > 0 else robot_manager.get_navigation_states()[0]

        if self.get_simulation_mode() and self.get_simulation_auto():
            current_state = 'auto'

        return current_state

    def set_navigation_state(self, navigation_state):
        """
        Sets the robot's navigation state based on the provided state name.

        Parameters:
            navigation_state (str): The name of the navigation state to set.
        """
        sim_mode = self.get_simulation_mode()
        if sim_mode:
            redis_server.set_value('pc.simulation.auto', navigation_state != 'normal')
        else:
            if navigation_state in self.get_navigation_states():
                redis_server.set_value('plc.monitor.state.' + navigation_state, True)

        # Control operations
        control_name = 'plc.control.state.' + navigation_state
        if navigation_state in self.get_navigation_states() and control_name in redis_server.variables.keys():
            # Pulse the state variable to trigger state change
            redis_server.set_value(control_name, True)
            time.sleep(0.5)
            redis_server.set_value(control_name, False)
            print("Pulsed %s" % control_name)

    def set_position_latlon(self, lat, lon):
        """
        Set the position of the robot based on latitude and longitude coordinates.

        :param lat: latitude coordinate
        :param lon: longitude coordinate
        :return: None
        """
        # Define the coordinate reference systems
        wgs84_crs = 'EPSG:4326'  # WGS 84
        utm_crs = 'EPSG:%d' % self.field.shp_geofence.gdf.crs.to_epsg()

        x, y = shp.transform_crs(wgs84_crs, utm_crs, [lat, lon])
        self.set_position(x, y)

    @staticmethod
    def set_position(x, y, yaw=None):
        robot_ref_state = redis_server.get_json_value("robot.ref.state")
        if robot_ref_state is None:
            # skip if there is no robot_ref_state
            return
        robot_ref_state["T"] = [x, y, 0.0]
        if yaw is not None:
            robot_ref_state["R"] = [0.0, 0.0, yaw]
        redis_server.set_json_value("robot.ref.state", robot_ref_state)

    @staticmethod
    def set_velocity(vx, omega):
        redis_server.set_value('plc.control.navigation.velocity.longitudinal', vx)
        redis_server.set_value('plc.control.navigation.velocity.angular', omega)

    @staticmethod
    def get_velocity():
        vx = redis_server.get_value('plc.control.navigation.velocity.longitudinal')
        omega = redis_server.get_value('plc.control.navigation.velocity.angular')

        return vx, omega

    @staticmethod
    def get_simulation_mode():
        """
        Get the current simulation mode from the Redis server.

        :return: The current simulation mode (str)
        """
        return redis_server.get_value('pc.simulation.active')

    @staticmethod
    def get_simulation_auto():
        return redis_server.get_value('pc.simulation.auto')

    def set_simulation_mode(self, active=True):
        redis_server.set_value('pc.simulation.active', active)
        # set position to first point of the traject
        if len(self.field.shp_traject.gdf):
            traject_points = robot_manager.field.shp_traject.gdf.geometry[0].coords

            first_point = Point(traject_points[0])
            second_point = Point(traject_points[1])
            path_orientation = shp.get_orientation(first_point, second_point)

            self.set_position(first_point.x, first_point.y, path_orientation)
        # navigation state back to normal when simulation mode is turned off
        if not active:
            self.set_navigation_state('normal')

    @staticmethod
    def set_simulation_speed_factor(factor):
        redis_server.set_value('pc.simulation.factor', factor)

    @staticmethod
    def get_simulation_speed_factor():
        return redis_server.get_value('pc.simulation.factor')

    @staticmethod
    def get_programming_mode():
        return redis_server.get_value('plc.monitor.substate.programming')

    @staticmethod
    def acknowledge_notification():
        redis_server.set_value('pc.execution.notification', '-')

    @staticmethod
    def update_field():
        redis_server.set_value('pc.field.updated', True)

    def status(self):
        return redis_server.get_json_value("robot.status")

    def context(self):
        redis_data = redis_server.get_n_json_value(["robot.center.state", "robot.ref.state", "robot.head.state",
                                                    "robot.contour", "hitch.states", "implement.states",
                                                    "navigation.controller.info"])
        r = dict()

        r['robot'] = {'contours': redis_data['robot.contour'],
                      'center': redis_data['robot.center.state']['point'],
                      'ref': redis_data['robot.ref.state']['point'],
                      'head': redis_data['robot.head.state']['point'],
                      'orientation': redis_data['navigation.controller.info']['heading']}
        # Add each hitch
        r['hitches'] = redis_data['hitch.states']

        # Add implements
        r['implements'] = redis_data['implement.states']

        # Add controller info
        r['controller_info'] = redis_data['navigation.controller.info']

        return r


robot_manager = RobotManager()
