# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

from typing import Any, Dict
import os
import toml


class Config:
    """
    Main configuration handler for Aqumen.
    Parses TOML config file into a Python dict and stores as data member self.config
    """

    def __init__(self, filename=None):
        config_file = os.getenv("AQUMEN_CONFIG") if not filename else filename
        if config_file is None:
            #raise EnvironmentError("The AQUMEN_CONFIG environment variable is not set")
            # use defaults
            self.config = {}
            self.set("config_name", "default")
            self.set("data.db_type", "sqlite")
            self.set("data.sqlite_dir", ":memory:")
            return
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"The file {config_file} does not exist")
        self.config = toml.load(config_file)

    def get(self, key, default=None):
        """
        Retrieve a confguration parameter specifying the key as a string.
        Parameters nested within groups can be referred to with a single string
        by putting a dot within group names, e.g. data.db_type
        """
        keys = key.split(".")
        val = self.config
        for k in keys:
            if k in val:
                val = val[k]
            else:
                return default
        return val

    def set(self, key, value):
        """
        Add a confguration parameter specifying the key as a string.
        Parameters nested within groups can be referred to with a single string
        by putting a dot within group names, e.g. data.db_type
        """
        keys = key.split(".")
        val = self.config
        for k in keys[:-1]:
            if k not in val:
                val[k] = {}
            val = val[k]
        val[keys[-1]] = value

    def save(self, filename):
        """
        Write current set of congiruation parameters to disk.
        """
        with open(filename, "w", encoding="utf-8-sig") as f:
            toml.dump(self.config, f)


_the_config = None


def _get_singleton() -> Config:
    """
    Singleton for the main config.
    """
    global _the_config
    if _the_config is None:
        _the_config = Config()
    return _the_config


def get(key: str, default: Any = None) -> Any:
    """
    Read a value given a key. If not found, return default
    """
    return _get_singleton().get(key, default)


def set_value(key: str, value: Any) -> None:
    """
    Save a value in the config under a key
    """
    return _get_singleton().set(key, value)


def as_dict() -> Dict[str, Any]:
    """
    Nested dictionary of configuration parameters
    """
    return _get_singleton().config
