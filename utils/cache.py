import os
import sys
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib
import subprocess
from .misc import in_directory
from .gerrit import generate_changeid

cache_dir = os.path.expanduser("~/.cache/yo")

def create_cache_dir():
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

def add_branch_cache(f, branch, issue=1308201):
     with open(f, mode="a", encoding="utf-8") as fp:
            fp.write("[\"" + branch + "\"]\n")
            fp.write("issue = %d\n" % (issue))
            fp.write("changeid = \"%s\"\n" % (generate_changeid(branch)))


def get_branch_cache(branch):
    create_cache_dir()
    f = cache_dir + "/branches.db"

    if not os.path.isfile(f):
        add_branch_cache(f, branch)

    with open(f, mode="rb") as fp:
        cache = tomllib.load(fp)

    try:
        return cache[branch]
    except KeyError:
        add_branch_cache(f, branch)
        with open(f, mode="rb") as fp:
            return tomllib.load(fp)[branch]
