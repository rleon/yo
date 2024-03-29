import os
import pwd
import sys
import subprocess
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib
from utils.cmdline import get_internal_fn

def get_config(section):
    """ Provide specific config section """
    profile = pwd.getpwuid(os.getuid())[0]
    config_f = get_internal_fn("profiles/" + profile + "/" + section + ".toml")
    try:
        with open(config_f, mode="rb") as fp:
            return tomllib.load(fp)
    except FileNotFoundError:
        exit("Failed to find %s config." % (section))
