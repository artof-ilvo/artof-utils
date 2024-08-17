from unittest import TestCase

import numpy as np

from artof_utils.schemas.state import State
import artof_utils.paths as paths
import json


class TestRobotManager(TestCase):
    def test_load_settings(self):
        # Arrange
        # - Load settings file
        with open(paths.platform_settings, 'r') as f:
            ref_settings = json.load(f)
        # - Load settings done as singleton
        from artof_utils.robot import robot_manager

        # Act
        # - Load settings with robot manager
        settings = robot_manager.platform_settings.model_dump()

        # Assert
        self.assertEqual(ref_settings.keys(), settings.keys())

    def test_load_field(self):
        # Arrange
        # - Load settings done as singleton
        from artof_utils.robot import robot_manager

        # Act
        field_name = robot_manager.field.name

        # Assert
        self.assertIsNotNone(field_name)

    def test_load_hitches(self):
        # Arrange
        # - Load settings done as singleton
        from artof_utils.robot import robot_manager

        # Act
        no_hitches = len(robot_manager.hitches.hitches)

        # Assert
        self.assertGreater(no_hitches, 0)

    # def test_load_navigation(self):
    #     # Arrange
    #     # - Load settings done as singleton
    #     from artof_utils.manager import robot_manager
    #
    #     # Act
    #     nav_mode = robot_manager.navigation.navigation_mode
    #
    #     # Assert
    #     self.assertGreater(nav_mode, 0)

    # def test_shape(self):
    #     # Arrange
    #     # - Load settings done as singleton
    #     from artof_utils.robot import robot_manager
    #     state = State({'T': [10, 10, 0], 'R': [0, 0, 180.0], 'T_cov': [0, 0, 0], 'R_cov': [0, 0, 0]})
    #
    #     # Act
    #     print(robot_manager.context())

    def test_set_simulation_mode(self):
        # Arrange
        # - Load settings done as singleton
        from artof_utils.robot import robot_manager
        from artof_utils.redis_instance import redis_server
        # Act
        robot_manager.set_position(0, 0)
        robot_ref_state_zero = redis_server.get_json_value("robot.ref.state")
        self.assertTrue(np.allclose(np.array(robot_ref_state_zero["T"][:2]), 0))

        robot_manager.set_simulation_mode(True)
        robot_ref_state = redis_server.get_json_value("robot.ref.state")

        first_traject_point = np.array(list(robot_manager.field.shp_traject.gdf.geometry[0].coords)[0])
        # Assert
        self.assertTrue(np.allclose(np.array(robot_ref_state["T"][:2]), first_traject_point))

    def test_stop_simulation_mode(self):
        # Arrange
        # - Load settings done as singleton
        from artof_utils.robot import robot_manager
        from artof_utils.redis_instance import redis_server
        # Act
        robot_manager.set_simulation_mode(False)
        # Assert
        self.assertEqual(redis_server.get_value('pc.simulation.active'), 0)

    def test_set_simulation_speed_factor(self):
        # Arrange
        # - Load settings done as singleton
        from artof_utils.robot import robot_manager
        from artof_utils.redis_instance import redis_server
        # Act
        robot_manager.set_simulation_speed_factor(0.5)
        # Assert
        self.assertEqual(redis_server.get_value('pc.simulation.factor'), 0.5)

    # def test_status(self):
    #     # Arrange
    #     # - Load settings done as singleton
    #     from artof_utils.robot import robot_manager
    #     # Act
    #     status = robot_manager.status()
    #     # Assert
    #     self.assertIsNotNone(status)
    #     self.assertTrue('fix' in status)
    #     self.assertTrue('power_level' in status)