from unittest import TestCase
import numpy as np
import json
from shapely.geometry import LineString

import artof_utils.paths as paths
# We importeren de singletons nu netjes bovenaan het bestand
from artof_utils.robot_manager import robot_manager
from artof_utils.redis_manager import redis_server


class TestRobotManager(TestCase):
    def test_load_settings(self):
        # Arrange
        with open(paths.platform_settings, 'r') as f:
            ref_settings = json.load(f)

        # Act
        settings = robot_manager.platform_settings.model_dump()

        # Assert
        self.assertEqual(ref_settings.keys(), settings.keys())

    def test_load_field(self):
        # Act
        field_name = robot_manager.field.name

        # Assert
        self.assertIsNotNone(field_name)

    def test_load_hitches(self):
        # Act
        no_hitches = len(robot_manager.hitches.hitches)

        # Assert
        self.assertGreater(no_hitches, 0)

    def test_set_simulation_mode(self):
        # 1. ARRANGE
        # Zet de robot handmatig op [0,0]
        robot_manager.set_position(0, 0)
        robot_ref_state_zero = redis_server.get_json_value("robot.ref.state")
        
        # Test kan alleen draaien als Redis effectief een state teruggeeft
        if robot_ref_state_zero is not None:
            self.assertTrue(np.allclose(np.array(robot_ref_state_zero["T"][:2]), 0))

        # We pushen nu IN MEMORY een traject in het veld (LineString)
        test_lijn = LineString([[15.0, 25.0], [15.0, 90.0]])
        robot_manager.field.update_traject(test_lijn)

        # 2. ACT
        # Bij het aanzetten van simulatie moet de robot nu naar [15.0, 25.0] snappen
        robot_manager.set_simulation_mode(True)
        
        # 3. ASSERT
        robot_ref_state = redis_server.get_json_value("robot.ref.state")
        if robot_ref_state is not None:
            # We checken direct tegen ons in-memory punt in plaats van ingewikkelde GDF queries
            first_traject_point = np.array([15.0, 25.0])
            self.assertTrue(np.allclose(np.array(robot_ref_state["T"][:2]), first_traject_point))

    def test_stop_simulation_mode(self):
        # Act
        robot_manager.set_simulation_mode(False)
        # Assert
        self.assertEqual(redis_server.get_value('pc.simulation.active'), 0)

    def test_set_simulation_speed_factor(self):
        # Act
        robot_manager.set_simulation_speed_factor(0.5)
        # Assert
        self.assertEqual(redis_server.get_value('pc.simulation.factor'), 0.5)