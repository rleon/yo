import os
from utils.git import *
from utils.misc import *
from utils.cache import get_ci_token
from utils.cmdline import get_internal_fn

def run_nbu_ci(rev):
    token = get_ci_token()
    mirror_kernel()
    with open(get_internal_fn('scripts/nbu-regression'), "r") as f:
        exec_on_remote("hpchead.lab.mtl.com",
                       args=["GIT_REPO=/.autodirect/swgwork/%s/src/kernel" % (os.getlogin()),
                             "RPM_DIR=/.autodirect/swgwork/%s/rpms" % (os.getlogin()),
                             "GIT_REVISION=%s" % (git_current_sha(rev)),
                             "JENKINS_TOKEN=%s" % (token), "SKIP_EMAIL=true",
                             "bash"], script=f)
        print("NBU CI regression started:")
        print("\thttps://nbuprod.blsm.nvidia.com/nbu-sw-upstream-linux-build/job/CI/job/NFS_SOURCE_CI/job/main/")
        exec_on_remote("hpchead.lab.mtl.com",
                       args=["find /.autodirect/swgwork/%s/rpms" % (os.getlogin()),
                             "-mindepth", "1", "-mtime", "+3", "-delete"])
