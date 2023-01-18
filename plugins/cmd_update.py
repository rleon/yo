"""YO cloud tools
"""
from utils.git import *
from utils.misc import get_project
from profiles import get_config

def update_linus_tag(tags, verbose):
     for remote, branches in tags.items():
         for branch in branches:
            tag = git_linus_tag(remote, branch[1])
            if git_same_branch(tag, branch[0]):
                continue

            prev = git_checkout_branch(branch[0], verbose)
            git_reset_branch(tag, verbose)
            git_checkout_branch(prev, verbose)

def rebase_branches(branches, verbose):
    curr = git_current_branch()
    for local, base in branches.items():
        if git_branch_contains(local, base):
            # It is already rebased
            continue

        git_checkout_branch(local, verbose)
        git_rebase_branch(base, verbose)

    git_checkout_branch(curr, verbose)

def merge_branches(branches, verbose):
    curr = git_current_branch()
    for local, pile in branches.items():
        git_checkout_branch(local, verbose)
        if not git_same_branch(local, pile[0]):
            git_reset_branch(pile[0], verbose)
        pile.pop(0)

        for branch in pile:
            if git_branch_contains(local, branch):
                continue

            git_merge_rr(branch, verbose)

    git_checkout_branch(curr, verbose)

#--------------------------------------------------------------------------------------------------------
def args_update(parser):
    parser.add_argument(
            "-v",
            "--verbose",
            dest="verbose",
            action="store_true",
            help="Be more verbose",
            default=False)

def cmd_update(args):
    """Update trees"""

    args.root = git_root()
    if args.root is None:
        exit()

    args.project = get_project(args)
    if args.project != "kernel":
        exit("Update is supported for kernel tree only.")

    config = get_config("update")
    git_remote_update(config["remotes"])
    update_linus_tag(config["tags"], args.verbose)
    rebase_branches(config["rebases"], args.verbose)
    merge_branches(config["merges"], args.verbose)
