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
        if ":29418/upstream/linux" in url:
            return remote

def git_push_gerrit(remote, commit, branch, topic, dry_run=False):
    cmd = ["push"]
    if dry_run:
        cmd += ["--dry-run"]

    git_call(cmd + [remote, '%s:refs/for/%s%%topic=%s' % (commit, branch, topic)])

def push_squash(remote, upto, base, branch, topic, issue, changeid, dry_run, verbose):
    with tempfile.TemporaryDirectory() as d:
        git_detach_workspace(d, verbose)

        with in_directory(d):
            git_reset_branch("%s/%s" % (remote, base), verbose)
            log = git_simple_output(['log', '-n', '100', '--abbrev=12',
                                     '--format=commit %h (\"%s\")', 'HEAD..', upto])

            try:
                git_merge_squash(upto, verbose)
            except subprocess.CalledProcessError:
                git_worktree_prune()
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

    git_worktree_prune()

def generate_changeid(branch="HEAD"):
    ps = subprocess.run(["git", "show", branch], check=True, capture_output=True)
    patchid = subprocess.run(["git", "patch-id", "--stable"], input=ps.stdout, capture_output=True)

    return patchid.stdout.decode('utf-8').strip().split()[0]
