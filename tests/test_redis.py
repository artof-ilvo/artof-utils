from unittest import TestCase
from artof_utils.schemas.state import State
from artof_utils.redis import RedisServer
from os import getenv
import artof_utils.paths as paths


class TestRedisServer(TestCase):
    def test_set_get_value_from_config(self):
        variables = {
            "pc.gps.fix": 5,
            "pc.gps.hrp_mode": 3,
        }

        redis_server = RedisServer(ilvo_path=paths.ilvo_path, host='127.0.0.1')
        for k, v in variables.items():
            self.assertTrue(redis_server.variable_in_config(k))
            redis_server.set_value(k, v)

        for k, v in variables.items():
            value = redis_server.get_value(k)
            self.assertEqual(v, value)

    def test_n_set_get_value_from_config(self):
        variables = {
            "random1": 15.0,
            "random2": 15.0,
        }
        redis_server = RedisServer(ilvo_path=paths.ilvo_path, host='127.0.0.1')
        redis_server.set_n_values(variables)

        r_variables = redis_server.get_n_values(list(variables.keys()))
        for k, v in r_variables.items():
            self.assertEqual(str(v), str(variables[k]))

    def test_n_set_get_value_partly_config(self):
        variables = {
            "pc.gps.fix": 5,
            "pc.gps.hrp_mode": 3,
            "random": 10.0
        }
        redis_server = RedisServer(ilvo_path=paths.ilvo_path, host='127.0.0.1')
        redis_server.set_n_values(variables)

        r_variables = redis_server.get_n_values(list(variables.keys()))
        for k, v in r_variables.items():
            self.assertEqual(str(v), str(variables[k]))

    def test_n_set_get_value_no_config(self):
        variables = {
            "random0": 20.0,
            "random1": 2.0,
            "random2": 4.0
        }
        redis_server = RedisServer(ilvo_path=paths.ilvo_path, host='127.0.0.1')
        redis_server.set_n_values(variables)

        r_variables = redis_server.get_n_values(list(variables.keys()))
        for k, v in r_variables.items():
            self.assertEqual(str(v), str(variables[k]))

    def test_set_get_json_value(self):
        j_orig = {
            "int": 1.0,
            "double": 10.0,
            "str": "str"
        }
        redis_server = RedisServer(ilvo_path=paths.ilvo_path, host='127.0.0.1')
        redis_server.set_json_value("json_obj", j_orig)

        j_read = redis_server.get_json_value("json_obj")
        self.assertEqual(str(j_read), str(j_orig))

    def test_set_get_json_state(self):
        d = {
            "R": [-0.0, 0.0, 40.0],
            "R_cov": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
            "T": [554579.00, 5648161.00, 0.0],
            "T_cov": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]}
        state = State(d)
        state_name = "robot.ref.state"

        redis_server = RedisServer(ilvo_path=paths.ilvo_path, host='127.0.0.1')
        redis_server.set_state(state_name, state)
        state_ = redis_server.get_state(state_name)

        print(f"state: {state}")
        print(f"state_: {state_}")
        assert state == state_, f"States are not equal!"

    def test_json_value_with_path(self):
        d = {
            "test": [
                {"nested_1": {
                    "json": 1
                }},
                {"nested_2": {
                    "json": 1
                }}
            ]
        }
        json_name = "test"

        redis_server = RedisServer(ilvo_path=paths.ilvo_path, host='127.0.0.1')
        redis_server.set_json_value(json_name, d)

        redis_server.set_json_value(json_name, 0, '$.test[0].nested_1.json')
        json_value_test = redis_server.get_json_value(json_name)

        print(f"json_value \'test\' before set: ", d)
        print(f"json_value \'test\' after set: ", json_value_test)
        # assert state == state_, f"States are not equal!"

    def test_load_variables(self):
        # Arrange
        # Act
        redis_server = RedisServer(ilvo_path=paths.ilvo_path)
        # Assert
        self.assertGreaterEqual(len(redis_server.variables), 0)
