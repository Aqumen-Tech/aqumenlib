# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

import sys
import logging
import pathlib
from datetime import datetime

CRITICAL = 50
FATAL = CRITICAL
ERROR = 40
WARNING = 30
WARN = WARNING
INFO = 20
DEBUG = 10
NOTSET = 0

_levelToName = {
    CRITICAL: "CRITICAL",
    ERROR: "ERROR",
    WARNING: "WARNING",
    INFO: "INFO",
    DEBUG: "DEBUG",
    NOTSET: "NOTSET",
}
_nameToLevel = {
    "CRITICAL": CRITICAL,
    "FATAL": FATAL,
    "ERROR": ERROR,
    "WARN": WARNING,
    "WARNING": WARNING,
    "INFO": INFO,
    "DEBUG": DEBUG,
    "NOTSET": NOTSET,
}


def init_logging(pyconfig: dict):
    """
    :param Config pyconfig:  configuration options parsed into python dict
    """
    if "logging" not in pyconfig:
        # print("No logging configured.")
        return
    cfg_dict = pyconfig["logging"]

    level = logging.ERROR
    if "level" in cfg_dict:
        lname = cfg_dict["level"]
        if lname not in _nameToLevel:
            raise KeyError(f"Configured log level not recongized: {lname}")
        level = _nameToLevel[lname]

    handlers = []

    if "console" in cfg_dict:
        console_set: str = cfg_dict["console"].lower()
        if console_set.startswith("y"):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S")
            console_handler.setFormatter(formatter)
            handlers.append(console_handler)

    if "log_dir" in cfg_dict:
        log_dir = pathlib.Path(cfg_dict["log_dir"])
        log_dir.mkdir(exist_ok=True)
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        invoker = pathlib.Path(sys.argv[0])
        log_file = log_dir / f"{current_time}_{invoker.name}.log"
        file_handler = logging.FileHandler(str(log_file))
        file_handler.setLevel(level)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    logging.basicConfig(level=level, handlers=handlers)
