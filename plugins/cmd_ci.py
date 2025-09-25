"""YO cloud tools
"""
import os
import subprocess
import argparse
import tempfile
from utils.git import *
from utils.misc import get_project, in_directory

def print_verbose_cmd(args, cmd):
    if args.verbose:
        print(' '.join(cmd))

def ynl(args):
    cmd = ["tools/net/ynl/ynl-regen.sh", "-f"]
    print_verbose_cmd(args, cmd)
    subprocess.run(cmd, stdout=subprocess.DEVNULL);

    cmd = ["make", "-s", "-C", "tools/net/ynl/", "W=1", "-j", str(args.num_jobs)]
    print_verbose_cmd(args, cmd)
    subprocess.call(cmd, stdout=subprocess.DEVNULL)

def checkpatch(args):
    cmd = ["./scripts/checkpatch.pl", "-q", "--no-summary", "-g", args.rev,
           "--max-line-length=80", "--codespell"]
    if args.gerrit:
        cmd += ["--ignore", "GERRIT_CHANGE_ID,FILE_PATH_CHANGES"]
    print_verbose_cmd(args, cmd)
    subprocess.call(cmd);

def coccicheck(args):
    for d in args.dirlist:
        cmd = ["make", "coccicheck", "MODE=report", "M=%s" %(d),  "-j", str(args.num_jobs)]
        print_verbose_cmd(args, cmd)
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT);

def check_parser_errors(out):
    found = False
    for line in out.stderr.split('\n'):
        if line.startswith("scripts") or line == '':
            # Fixup to https://lore.kernel.org/lkml/1521810279-6282-3-git-send-email-yamada.masahiro@socionext.com/
            continue
        print(line)
        found = True

    if found:
        exit()

def check_filter_errors(args, out):
    found = False
    # sparse output everything on stderr
    for line in out.stderr.split('\n'):
        l = line.split(":")
        try:
            if l[0] not in args.files:
                continue
            if not l[1].isdigit():
                continue
        except IndexError:
            if not l:
                print(line)
                found = True
            continue
        cmd = ["blame", l[0], "-L%s,%s" %(l[1], l[1]), "-l", "-s"]
        blame = git_simple_output(cmd).split()[0]
        if args.rev == blame:
            print(line)
            found = True

    if (found):
        exit()

def warnings(args, tool_cmd=None, arch="x86_64"):
    base_cmd = ["make", "-s", "ARCH=%s" %(arch), "-j", str(args.num_jobs)]
    cmd = base_cmd + ["clean"]
    print_verbose_cmd(args, cmd)
    subprocess.call(cmd)
    if tool_cmd:
        base_cmd += tool_cmd

    cmd = base_cmd + [args.config]
    print_verbose_cmd(args, cmd)
    subprocess.call(cmd)

    cmd = base_cmd + ["W=1"] + args.dirlist
    print_verbose_cmd(args, cmd)
    out = subprocess.run(cmd, encoding='utf-8', capture_output=True)
    if not args.includes:
        check_parser_errors(out)
    else:
        check_filter_errors(args, out)

def warnings_32b(args):
    warnings(args, arch="i386")

def clang(args):
    warnings(args, tool_cmd=["CC=clang"])

def smatch(args):
    warnings(args, tool_cmd=["CHECK=smatch", "C=2"])

def sparse(args):
    warnings(args, tool_cmd=["CHECK=sparse", "C=2", "CF='-fdiagnostic-prefix -D__CHECK_ENDIAN__'"])

def rust(args):
    warnings(args, tool_cmd=["LLVM=1"])

def build_dirlist(args):
    cmd = ["show", "--name-only", "--oneline", args.rev]
    files = git_simple_output(cmd).split('\n')
    # Remove subject line
    files = list(filter(None, files[1:]))
    # Leave only directories which we know how to check
    supported = ("arch", "block", "crypto", "fs", "init", "ipc", "kernel",
        "lib", "mm", "drivers", "net", "security", "sound", "virt")
    dirlist = set()
    includes = set()
    for f in files:
        if f.startswith(supported):
            dirlist.add(os.path.join(os.path.dirname(f), ''))
        if f.endswith(".h"):
            includes.add(f)

    if includes and not dirlist:
        # Let's do smart guess and try to check subsystems,
        # which we are changing most of the time.
        # TODO: optimize it, this condition adds a lot of delay
        dirlist.add("drivers/infiniband/")
        dirlist.add("drivers/net/ethernet/mellanox/")
        dirlist.add("drivers/nvme/")
        dirlist.add("drivers/fwctl/")
        dirlist.add("drivers/iommu")
        dirlist.add("net/core/")
        dirlist.add("net/devlink/")
        dirlist.add("net/xfrm/")
        dirlist.add("kernel/dma/")

    args.dirlist = list(dirlist)
    args.includes = list(includes)
    args.files = [f for f in files if f not in args.includes]

def set_gerrit_flag(args):
    cmd = ["branch", "--format=%(refname:short)", "--contains", args.rev]
    branches = git_simple_output(cmd).split()
    for branch in branches:
        if not branch.startswith("m/"):
            args.gerrit = False
            return

    args.gerrit = True

#--------------------------------------------------------------------------------------------------------
def args_ci(parser):
    parser.add_argument(
            "rev",
            nargs='?',
            help="SHA1 to check",
            default = "HEAD")
    parser.add_argument(
            "-v",
            "--verbose",
            dest="verbose",
            action="store_true",
            help="Be more verbose",
            default=False)

def cmd_ci(args):
    """Run local CI"""

    args.root = git_root()
    if args.root is None:
        exit()

    args.project = get_project(args)
    if args.project != "kernel":
        exit("CI is supported for kernel tree only.")

    args.num_jobs = len(os.sched_getaffinity(0)) * 2

    git_call(["--no-pager", "log", "--oneline", "-n1", args.rev])

    set_gerrit_flag(args)
    build_dirlist(args)

    # In-tree checks
    checkpatch(args)

    with tempfile.TemporaryDirectory() as d:
        git_detach_workspace(d, args.verbose, args.rev)
        with in_directory(d):
            # Semantic checks, no need different configs
            coccicheck(args)
            ynl(args)

            base_configs = ["allyesconfig", "allnoconfig", "allmodconfig", "alldefconfig"]
            extra_configs = ["tinyconfig", "debug.config", "kvm_guest.config", "xen.config",
                             "hardening.config", "nopm.config"]
            # Compilation checks
            for config in base_configs + extra_configs:
                args.config = config

                warnings(args)
                warnings_32b(args)
                clang(args)

            for config in base_configs:
                args.config = config

                smatch(args)
                sparse(args)

            # We check one arch and one config only
            args.config = "rust.config"
            rust(args)

    git_worktree_prune()

