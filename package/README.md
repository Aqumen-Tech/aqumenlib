## AQUMEN is a financial analytics SDK

### Installation

Typical steps to install AQUMEN SDK are:

 - install Python and create an environment using Python 3.11 or later
 - pip install prerequisites from provided requirements.txt
 - pip install provided Python wheel file
 - (optional) create a config file - minimal example is below
 - (optional) set up an environment variable AQUMEN_CONFIG to point to this config file 
 - (optional) pip install examples/requirements.txt to run examples
 
### Minimal config example

Configuration can be provided using TOML file format. See https://toml.io/ for syntax.
Note that config file is optional. By default in-memory SQLite will be used and logging will be disabled.

```
config_name = "sample config"

[data]
db_type = "sqlite"
sqlite_dir = ":memory:" # use sqlite in memory or specify a folder for db files

[logging]
level = "INFO" # https://docs.python.org/3/library/logging.html#logging-levels
console = "NO" # should also write to stdout? yes or not
log_dir = "C:/Temp/AqumenLog" 
```
