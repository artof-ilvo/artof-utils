from artof_utils.singleton import Singleton
from artof_utils.schemas.implement import Implement
from glob import glob
from os import path, remove
import artof_utils.paths as paths
import json


class ImplementManager(metaclass=Singleton):
    @property
    def implements(self):
        return [Implement.load(path.basename(implement_name).replace('.json', ''))
                for implement_name in glob(path.join(paths.implements, '*.json'))]

    @staticmethod
    def update_implement(name, implement: Implement):
        implement_file_path = path.join(paths.implements, '%s.json' % name)
        with open(implement_file_path, 'w') as json_file:
            json.dump(implement.context, json_file, indent=4)

    @staticmethod
    def add_implement(name, implement: Implement):
        ImplementManager.update_implement(name, implement)

    @staticmethod
    def remove_implement(name):
        implement_file_path = path.join(paths.implements, '%s.json' % name)
        if path.exists(implement_file_path):
            remove(implement_file_path)

    @staticmethod
    def get_implement(name):
        return Implement.load(name)


implement_manager = ImplementManager()
