import os
import subprocess

def git_call(args):
    """Run git and display the output to the terminal"""
    return subprocess.check_call([
        'git',
    ] + args)

def git_output(args, mode=None, null_stderr=False, input=None):
    """Run git and return the output"""
    if null_stderr:
        with open("/dev/null") as F:
            o = subprocess.check_output(
                [
                    'git',
                ] + args, stderr=F, input=input)
    else:
        o = subprocess.check_output(
            [
                'git',
            ] + args, input=input)
    if mode == "raw":
        return o
    elif mode == "lines":
        return o.splitlines()
    elif mode is None:
        return o.strip()
    else:
        raise ValueError("Bad mode %r" % (mode))

def git_simple_output(args):
    """Run git and return the output"""
    try:
        o = subprocess.check_output(['git', ] + args)
    except subprocess.CalledProcessError:
        return None

    return o.strip().decode("utf-8")

def git_root():
     """Return the top of the source directory we are currently in"""
     try:
         res = git_output(
             [
                 "rev-parse",
                 "--is-inside-work-tree",
                 "--is-inside-git-dir",
                 "--is-bare-repository",
                 "--absolute-git-dir",
                 "--show-cdup",  # must be last, may not print
             ],
             mode="lines")
     except subprocess.CalledProcessError:
         return None

     assert (len(res) == 5 or len(res) == 4)

     if res[0] == b"true":
         # The use of cdup and PWD means we return the path with any symlinks
         # intact.
         cwd = os.environ.get("PWD")
         if cwd is None:
             cwd = os.getcwd()
         return os.path.normpath(os.path.join(cwd, res[4].decode()))

     if res[1] == b"true":
         if res[2] == b"true":
             return res[3].decode()
         return os.path.normpath(os.path.join(res[3].decode(), ".."))

     return None

def git_push(remote, branches, force=False, dry_run=False):
    cmd = ["push"]
    if force:
        cmd += ["-f"]
    if dry_run:
        cmd += ["--dry-run"]

    git_call(cmd + [remote] + branches)

def git_same_content(a, b, strict=False):
    if a == b:
        return True

    try:
        if strict:
            l = git_current_sha(a)
            r = git_current_sha(b)
            if l != r:
                return False
        else:
            git_call(["diff", "--quiet", "%s..%s" % (a, b)])
    except subprocess.CalledProcessError:
        return False

    return True

def git_branch_contains(local_br, remote_br):
    res = git_output(["branch", "--contains", "%s" % (remote_br),
                      "--format=%(refname:short)"],
                     mode="lines")

    local_br = local_br.strip()
    for branch in res:
        branch = branch.decode().strip()
        if local_br == branch:
            return True

    return False

def git_remote_update(remotes=None):
    if remotes is None:
        remotes = ["all"]

    if type(remotes) is not list: remotes = [ remotes ]

    git_call(["remote", "update"] + remotes)

def git_linus_tag(remote, remote_br):
    tag = git_output(["log", "--pretty=format:%H", "-1",
                      "--author=Torvalds", "--no-merges", "%s/%s" % (remote, remote_br),
                      "--", "Makefile"])
    tag = git_output(["describe", tag.decode()])
    return tag.decode().strip()

def git_reset_branch(commit, verbose=False):
    """Reset to specific commit"""
    cmd = ["reset", "--hard"]
    if not verbose:
        cmd += ["-q"]

    git_call(cmd + [commit])

def git_current_branch():
    return git_output(["symbolic-ref", "--short", "-q", "HEAD"]).decode()

def git_current_sha(branch="HEAD"):
    return git_output(["rev-parse", "--short", "-q", branch]).decode()

def git_checkout_branch(branch=None, verbose=False):
    """Checkout specific branch and return previous branch"""
    prev = git_current_branch()
    if prev is None:
        exit("You are not in any branch, exciting ...");

    if branch is None:
        return prev;

    if prev != branch:
        cmd = ["checkout"]
        if not verbose:
            cmd += ["-q"]

        git_call(cmd + [branch])
    return prev

def git_same_branch(a, b):
    if a == b:
        return True;

    l = git_output(["log", "--pretty=format:%H", "-1", a])
    r = git_output(["log", "--pretty=format:%H", "-1", b])
    return l == r

def git_rebase_branch(base, verbose=False):
    cmd = ["rebase"]
    if not verbose:
        cmd += ["-q"]

    git_call(cmd + [base])

def git_merge_rr(commit, verbose=False):
    try:
        cmd = ["merge", "--no-ff", "--no-edit", "--rerere-autoupdate"]
        if not verbose:
            cmd += ["-q", "--no-progress"]
            git_output(cmd + [commit])
        else:
            git_call(cmd + [commit])
    except subprocess.CalledProcessError:
        status = git_simple_output(["status"])
        for line in status.splitlines():
            if "deleted by us:" in line:
                line = line.split(':')
                git_call(["rm", str(line[1].lstrip())])

        diff = git_output(["rerere", "diff"])
        num_of_lines = len(diff.splitlines())
        if num_of_lines > 1:
            exit("Fix rebase conflict, continue manually and rerun script once you are done.")

        # Add removed files
        git_call(["add", "--update"])
        cmd = ["commit", "--no-edit"]
        if not verbose:
            cmd += ["-q"]

        git_call(cmd)

def git_merge_squash(branch, verbose=False):
    cmd = ["merge", "--squash", "--ff"]
    if not verbose:
        cmd += ["-q",  "--no-progress"]
        git_output(cmd + [branch])
    else:
        git_call(cmd + [branch])

def git_find_base(remote, current, branches=["rdma-rc-mlx",
                                             "rdma-next-mlx",
                                             "net-next",
                                             "net"]):
    commits = 100000000
    best = ""

    for branch in branches:
        sha = git_simple_output(["merge-base", current,
                                 "%s/%s" % (remote, branch)])
        res = git_simple_output(["log", "--oneline", "--single-worktree",
                                 "%s..%s" % (sha, current)])
        count = len(res.split())
        if (count < commits):
            commits = count
            best = branch

    return best

def git_detach_workspace(path, verbose=False):
    cmd = ["worktree", "add", "--detach"]
    if not verbose:
        cmd += ["-q"]

    git_call(cmd + [path])

def git_worktree_prune():
    git_call(["worktree", "prune"])

def git_commit_from_file(fname, verbose=False):
    cmd = ["commit", "--allow-empty", "--no-edit"]
    if not verbose:
        git_output(cmd + ["-q", "-s", "-F", fname])
    else:
        git_call(cmd + ["-s", "-F", fname])

def git_author_name():
    git_simple_output(["config", "user.name"])

def git_author_email():
    git_simple_output(["config", "user.email"])
