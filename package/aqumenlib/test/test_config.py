# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

import pathlib
import aqumen.config as cfg

this_script_full_path = pathlib.Path(__file__).parent.resolve()


def test_config():
    """
    Test loading of standard config parameters.
    """
    c = cfg.Config(str(this_script_full_path / ".." / ".." / ".." / "config.toml"))
    assert c.config["config_name"] == "sample config"
    assert c.config["data"]["db_type"] == "sqlite"
    assert c.get("data.db_type") == "sqlite"
    assert c.get("config_name") == "sample config"
    c.set("abc", 12)
    assert c.get("abc") == 12
    c.set("xyz.abc", "a")
    assert c.get("xyz.abc") == "a"
    assert c.config["xyz"]["abc"] == "a"
    # logging.info(c.config)
