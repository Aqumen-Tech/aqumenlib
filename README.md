## AQUMEN is a financial analytics SDK for pricing and risk

- "package" folder contains Aqumen's main Python library, which can be packaged as a wheel
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

then install the Python modules from package folder in this environment. From cmd terminal on Windows, you could use
```
cd package
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
cd D:\aqumen\aqumenlib\examples
cmd
```

or on Linux something like this bash script:
```
. /home/username/bin/venv310/bin/activate
export AQUMEN_CONFIG=/home/username/dev/AqumenConfig/aqm_cfg_dev.toml
cd /home/username/dev/aqumenlib/examples
```

### Generating installation packages

Hatchling is being used as Python packaging tool.

To generate the installation packages, from  the package folder run this command:

```
python -m build
```

which should produce the following output:
```
* Creating virtualenv isolated environment...
* Installing packages in isolated environment... (hatchling)
* Getting build dependencies for sdist...
* Building sdist...
* Building wheel from sdist
* Creating virtualenv isolated environment...
* Installing packages in isolated environment... (hatchling)
* Getting build dependencies for wheel...
* Building wheel...
Successfully built aqumenlib-0.1.0.tar.gz and aqumenlib-0.1.0-py3-none-any.whl
```

The tar.gz file is a source distribution whereas the .whl file is a built distribution. 
Newer pip versions preferentially install built distributions, but will fall back to source distributions if needed. 
AQumen SDK package is compatible with Python on any platform so only one built distribution is needed.

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

