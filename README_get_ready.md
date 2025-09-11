## python the first time

### Install the python interpreter
On windows download the actual python interpreter from python.org. Do not use the automatic windows installer to install python. On Linux install python with the package manager of your os.

### Create a virtual python environment
This has only to be done once to create the virtual environment
```python3 -m venv .venv```

### init the python environment
This is needed every time you open the shell

#### on linux systems
```source .venv/bin/activate```

#### on windows systems
```.venv\Scripts\activate```


### install the required packages
This has only to be done once
```pip install -r requirements.txt```


