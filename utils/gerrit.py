import os
import tempfile
import subprocess
from utils.misc import in_directory
from .git import *

def get_gerrit_remote():
    """TODO: support other profiles than kernel"""
    remotes = git_output(["remote"]).decode().split()
    for remote in remotes:
        url = git_output(["remote", "get-url", "--push", remote]).decode()
        if ":12023/upstream/linux" in url:
            return remote

def get_gerrit_info(remote):
    url = git_output(["remote", "get-url", remote]).decode()
    host = url.split("@")[1].split(":")[0]
    port = int(url.split("@")[1].split(":")[1].split("/")[0])
    project = "upstream/linux"

    return host, port, project


def git_push_gerrit(remote, commit, branch, topic, dry_run=False):
    cmd = ["push"]
    if dry_run:
        cmd += ["--dry-run"]

    git_call(cmd + [remote, '%s:refs/for/%s%%topic=%s' % (commit, branch, topic)])

def build_and_push(remote, upto, base, branch, topic, issue, changeid, dry_run, verbose):
    git_reset_branch("%s/%s" % (remote, base), verbose)
    log = git_simple_output(['log', '-n', '10', '--abbrev=12',
                             '--format=commit %h (\"%s\")', 'HEAD..', upto])

    try:
        git_merge_squash(upto, verbose)
    except subprocess.CalledProcessError:
        return

    with tempfile.NamedTemporaryFile('w') as F:
        F.write('%s testing\n\n%s\n\nIssue: %s\nChange-Id: %s\n'
                % (branch, log, issue, changeid))
        F.flush()

        try:
            git_commit_from_file(F.name, verbose)
        except subprocess.CalledProcessError:
            # nothing to commit, working tree clean
            pass

        try:
            git_push_gerrit(remote, "HEAD", base, topic, dry_run)
        except subprocess.CalledProcessError:
            # nothing to commit, working tree clean
            pass


def git_push_squash_gerrit(remote, upto, base, branch, topic, issue, changeid, dry_run, verbose):
    if type(upto) is not list: upto = [ upto ]
    if type(base) is not list: base = [ base ]
    if type(branch) is not list: branch = [ branch ]
    if type(topic) is not list: topic = [ topic ]
    if type(issue) is not list: issue = [ issue ]
    if type(changeid) is not list: changeid = [ changeid ]

    with tempfile.TemporaryDirectory(prefix="kernel-") as d:
        git_detach_workspace(d, verbose)

        with in_directory(d):
            for up, ba, br, to, iss, ch in zip(upto, base, branch, topic, issue, changeid):
                build_and_push(remote, up, ba, br, to, iss, ch, dry_run, verbose)

    git_worktree_prune()

def generate_changeid(branch="HEAD"):
    ps = subprocess.run(["git", "show", branch], check=True, capture_output=True)
    patchid = subprocess.run(["git", "patch-id", "--stable"], input=ps.stdout, capture_output=True)

    return "I%s" % (patchid.stdout.decode('utf-8').strip().split()[0])
