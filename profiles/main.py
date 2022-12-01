import os
import pwd
import subprocess
from .rdma import *

def guess_profile():
    # There is no need in smart code here,
    # this is special utility for certain people
    # just guess profile by their username

    return pwd.getpwuid(os.getuid())[0]

def get_profile(profile = None):
    """Factory Method"""
    profiles = {
            "leonro": LRProfile,
    }
    if profile is None:
        profile = guess_profile()

    try:
        return profiles[profile]()
    except KeyError:
        return None
