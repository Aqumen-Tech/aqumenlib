## AQUMEN is a financial analytics framework for pricing and risk

### Motivation

AQUMEN is intended to make it easy to integrate financial analytics with other systems and solutions.
The typical user is a developer who need pricing and risk engine for derivatives and fixed income
instruments, but does not want to spend a great deal of time learning the low level
financial framework. 

As such, the focus is on ease of use and ease of intergration. Under the hood, QuantLib is used
extensively for the underlying mathematical underpinning of the pricing models.

Some of key features of the framework are:

- Serialization of all objects so that pricers or models can be saved as JSON objects and reconstructed elsewhere
- Built-in instrument symbology and a data model that naturally maps to that of market data vendors
- Built-in standard market conventions for a variety of commonly traded markets
- Support for concepts like trade, product, security, position, pricer, etc - which typically exist in systems but not in quant libraries
- Blotter-friendly pricers wtih universally consistent result types
- Ease of setting up CSA-differentiated discounting models
- Instrument classification and convenient one-line calculators for risks (both sensitivy and scenario driven)


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

## Developing for Aqumen 

At top level, there are two main folders 
- "package" folder contains Aqumen's main Python library, which can be packaged as a wheel
- "examples" folder contains some runnable examples.


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

