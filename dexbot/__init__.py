import pathlib
import os
from appdirs import user_config_dir

APP_NAME = "dexbot"
VERSION = '0.1.12'
AUTHOR = "codaone"
__version__ = VERSION


config_dir = user_config_dir(APP_NAME, appauthor=AUTHOR)
config_file = config_dir + "/config.yml"

default_config = """
node: wss://bitshares.openledger.info/ws
workers: {}
"""

if not os.path.isfile(config_file):
    pathlib.Path(config_dir).mkdir(parents=True, exist_ok=True)
    with open(config_file, 'w') as f:
        f.write(default_config)
        print("Created default config file at {}".format(config_file))

