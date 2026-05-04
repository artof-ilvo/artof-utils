import json
import redis
from os import path
from artof_utils.singleton import Singleton
from artof_utils.schemas.state import State


class RedisServer(metaclass=Singleton):
    previous_rt_dict: dict = {}

    def __init__(self, ilvo_path="", host: str = '127.0.0.1', port: int = 6379):
        self.variables = dict()

        if ilvo_path:
            config_path = path.join(ilvo_path, 'config.json')
            assert path.isfile(config_path), "'%s' is not an existing file" % config_path
            with open(config_path, mode='r') as json_file:
                self.config = json.load(json_file)

            types_path = path.join(ilvo_path, 'types.json')
            assert path.isfile(types_path), "'%s' is not an existing file" % types_path
            with open(types_path, mode='r') as json_file:
                self.types = json.load(json_file)

            self.load_variables("plc.monitor", self.config["variables"]["plc"]["monitor"])
            self.load_variables("plc.control", self.config["variables"]["plc"]["control"])
            self.load_variables("pc", self.config["variables"]["pc"])

            # A problem for the CI/CD
            # if "redis" in self.config["protocols"]:
            #     host = self.config["protocols"]["redis"]["ip"]
            #     port = self.config["protocols"]["redis"]["port"]

        self.r = redis.Redis(host=host, port=port)
        print('Connection to redis server host: %s:%d done!' % (host, port))

    def variable_in_config(self, name):
        return len(self.variables.keys()) > 0 and name in self.variables.keys()

    def load_variables(self, name: str, variables: dict):
        for key, variable_type in variables.items():
            if isinstance(variable_type, str):
                if variable_type in self.types:
                    self.load_variables(name + '.' + key, self.types[variable_type])
                else:
                    if "array" in variable_type:
                        array_type = variable_type.split(" of ")[-1]
                        array_size_str = variable_type.split(" of ")[0].split("[")[-1].replace("]", "")
                        array_size = int(array_size_str)

                        for i in range(array_size):
                            variable_name = name + '.' + key + '.' + str(i)
                            self.variables[variable_name] = {"type": array_type}
                    else:
                        variable_name = name + '.' + key
                        self.variables[variable_name] = {"type": variable_type}
            else:
                self.load_variables(name + '.' + key, variable_type)

    def convert_dtype(self, value: str, variable: str):
        """
        Convert the redis value to the prefered data type
        :param value: string of the redis value
        :param variable: string of the complete variable name
        :return: the value in the correct datatype
        """
        if value == "(nil)" or value is None:
            value = None

        var_type = "string"
        if self.variable_in_config(variable):
            var_type = self.variables[variable]["type"]

        if var_type in ["float", "double"]:
            try:
                val = float(value)
            except TypeError:
                val = 0.0
        elif 'int' in var_type:
            try:
                val = int(float(value))
            except TypeError:
                val = 0
        elif var_type in ["bool"]:
            try:
                val = bool(int(value))
            except TypeError:
                val = False
            except ValueError:
                v = False if value is None else value.decode()
                val = (v == "1" or v.lower() == "true")

        elif var_type in ["string"]:
            try:
                val = "" if value is None else value.decode()
            except TypeError:
                val = "-"
        else:
            try:
                val = value
            except TypeError:
                val = False
        return val

    def set_value(self, name, value) -> None:
        """
        Set the value of one parameter
        :return: None
        """
        var_name = name
        value_str = ('true' if value else 'false') if isinstance(value, bool) else str(value)
        if not self.r.set(var_name, value_str):
            print("Note: Setting variable \'%s\' to value \'%s\' failed" % (var_name, value_str))

    def set_n_values(self, variables: dict) -> None:
        """
        Set multile variables at the same time
        :param variables: dictionary containing 'variable' 'value' key value pairs
        :return: None
        """
        variables = {var: ('true' if val else 'false') if isinstance(val, bool) else str(val)
                     for var, val in variables.items()}
        self.r.mset(variables)

    def get_all_values(self) -> dict:
        """
        Get all variable values from the variables in the configuration file
        :return: dict
        """
        all_variables = list(self.variables.keys())
        d = self.get_n_values(all_variables)

        return d

    def get_value(self, name: str):
        var_name = name
        value_str = self.r.get(var_name)
        return self.convert_dtype(value_str, var_name)

    def get_n_values(self, variables: list[str]) -> dict:
        """
        Get multiple variables at once
        :param variables: list with all variables names of values want
        :return: dict with all variables values
        """
        values = self.r.mget(variables)
        d = {var: self.convert_dtype(val, var) for val, var in zip(values, variables)}

        return d

    def get_json_value(self, var_name: str) -> dict:
        """
        Get json object
        :param var_name: Variable name
        :return: read json object as dictionary
        """
        ret = self.r.json().get(var_name)
        if ret == "(nil)":
            return {}

        return ret

    def get_n_json_value(self, var_names: list, path_: str = '$') -> dict:
        """
        Get n json values
        :param var_names: List of variables to get
        :param path_: JSONpath to variables default is root
        :return: List of dictionaries
        """
        val = self.r.json().mget(var_names, path_)
        val_dict = {var: (v[0] if v is not None else v) for var, v in zip(var_names, val)}
        return val_dict

    def get_state(self, state_name: str):
        return State(self.get_json_value(state_name))

    def set_state(self, state_name: str, state: State):
        self.set_json_value(state_name, state.model_dump())

    def set_json_value(self, var_name: str, value, json_path='$'):
        """
        Set json object
        :param json_path: path to json value
        :param var_name: Variable name
        :param value: write json object as dictionary
        :return: None
        """
        self.r.json().set(var_name, json_path, value)
