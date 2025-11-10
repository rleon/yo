import os
import sys
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib
import requests
import subprocess
from .misc import in_directory
from .gerrit import generate_changeid
from .cmdline import query_user_pass

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

def add_cookie_cache(f):
    username, password = query_user_pass('http://linux-cloud.mellanox.com/')
    payload = {
            'username': username,
            'pass': password
    }

    headers = {'Cache-Control' : 'no-cache'}
    headers.update({'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/111.0'})
    headers.update({'Referer' : 'http://linux-cloud.mellanox.com/'})

    cookie = None
    with requests.session() as c:
        c.post('http://linux-cloud.mellanox.com/login', data=payload, headers=headers)
        if c.cookies.get('cloud_token') is not None:
            cookie = 'session=%s; cloud_token=%s' % (c.cookies.get('session'), c.cookies.get('cloud_token'))

    if cookie is None:
        exit("Failed to get cookie")

    with open(f, mode="a", encoding="utf-8") as fp:
        fp.write("cookie = \'%s\'\n" % (cookie))

def get_cloud_cache():
    create_cache_dir()
    f = cache_dir + "/cloud.db"

    if not os.path.isfile(f):
        add_cookie_cache(f)

    with open(f, mode="rb") as fp:
        cache = tomllib.load(fp)

    try:
        cache['cookie']
    except KeyError:
        add_cookie_cache(f)
        with open(f, mode="rb") as fp:
            return tomllib.load(fp)

    return cache

def get_ci_token():
    create_cache_dir()
    f = cache_dir + "/ci.db"

    if not os.path.isfile(f):
        exit("Please generate CI token https://nbuprod.blsm.nvidia.com/nbu-sw-upstream-linux-build and store it in ~/.cache/yo/ci.db")

    with open(f, mode="rb") as fp:
        cache = tomllib.load(fp)

    try:
        return cache['token']
    except KeyError:
        exit("Please write token in format: token = '123'")
