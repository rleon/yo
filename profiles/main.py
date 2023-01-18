import os
import pwd
import subprocess
from .rdma import *

def get_config(section):
    """ Provide specific config section """
    profiles = {
            "leonro": LRProfile,
    }

    profile = pwd.getpwuid(os.getuid())[0]
    try:
        return getattr(profiles[profile](), section)
    except AttributeError:
        exit("Failed to find %s config." % (section))
