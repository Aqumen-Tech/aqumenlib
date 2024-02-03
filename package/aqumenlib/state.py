# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

from typing import Any, Dict
from aqumenlib.namedobject import NamedObject


class StateManager:
    """
    Class that manages created objects in process memory.
    Can act as LRU cache if configured as such.
    """

    _objects: Dict[str, Dict[str, NamedObject]] = {}  # static variable to hold objects

    @staticmethod
    def store(obj_type: type, obj: NamedObject) -> None:
        """Store an object by name, segregated by its type."""
        obj_type_name = obj_type.__name__
        if obj_type_name not in StateManager._objects:
            StateManager._objects[obj_type_name] = {obj.get_name(): obj}
            return
        else:
            StateManager._objects[obj_type_name][obj.get_name()] = obj

    @staticmethod
    def get(obj_type: type, name: str) -> Any:
        """
        Retrieve an object by name and type.
        Returns None if not found.
        """
        obj_type_name = obj_type.__name__
        return StateManager._objects.get(obj_type_name, {}).get(name, None)
