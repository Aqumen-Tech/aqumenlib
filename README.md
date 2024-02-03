## AQUMEN is a financial analytics SDK for pricing and risk

- "package" folder contains Aqumen's main Python library, which can be packaged as a pip wheel
- "examples" folder contains some runnable examples.
- To change setting for logging or databse management, one can provide a config file. The steps are:
    -  must be set 
    - modify example config in config.toml and save as a new file
    - set environment variable AQUMEN_CONFIG and point it to this file
        - e.g. on Windows ```set AQUMEN_CONFIG=C:\aqumen\config.toml```
        - or on Linux ```export AQUMEN_CONFIG=$HOME\aqumen\config.toml```

## Developing for Aqumen 

### Setting up Python environment

to run while developing in VS code or similar, create a virtual environment, e.g.:
```
python -m venv "aqumen\venv"
aqumen\venv\Scripts\activate.bat
```

then install the Python package from aqm/python/ in this environment. From cmd terminal on Windows, you could use
```
cd aqumen\package\
pip install -r requirements.txt
pip install -e .
```
then choose this environment in VS code as Python interpreter.

To make it easier to use this environment from command line, you could create bat script for Windows, like this:

```
@echo off
@echo off
call D:\aqumen\venv\Scripts\activate.bat
set AQUMEN_CONFIG=D:\aqumen\aqm_config.toml
cd D:\aqumen\aqumen\scripts
cmd
```

or on Linux something like this bash script:
```
. /home/username/bin/venv310/bin/activate
export AQUMEN_CONFIG=/home/username/dev/AqumenConfig/aqm_cfg_dev.toml
cd /home/username/dev/aqumen/scripts
```

### Setting up development tools

Black formatter is used to standardize code style. To enable it to run automatically on git commit, run
```
pre-commit install
```
from the command line using above environment.

Sample launch.json file for VS Code
```
{
    "configurations": [
        {
            "name": "Python: Current File",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal",
            "justMyCode": true,
            "env": {"AQUMEN_CONFIG" : "D:/aqumen/aqm_config.toml"},
            //
            //"args": ["-myargs"]
        }
    ]
}
```

