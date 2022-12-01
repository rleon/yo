"""YO cloud tools
"""
from utils.cmdline import query_yes_no
from utils.git import *
from profiles import get_profile

def set_remotes(remotes):
    for remote, urls in remotes.items():
        git_call(["remote", "add", remote, urls[0]])
        cmd = ["remote", "set-url", "--push", remote]
        try:
            url = urls[1]
        except IndexError:
            url = urls[0]

        git_call(cmd + [url])

def create_branches(branches):
    for branch, base in branches.items():
        curr = git_current_branch()
        print(curr, branch)
        if curr == branch:
            git_reset_branch(base)
        else:
            git_call(["branch", branch, base])

#--------------------------------------------------------------------------------------------------------
def args_setup(parser):
    parser.add_argument(
            "-y",
            "--assume-yes",
            dest="yes",
            action="store_true",
            help="Automatically answer yes for all questions",
            default=False)

def cmd_setup(args):
    """Setup remotes"""

    args.root = git_root()
    if args.root is None:
        exit()

    if args.yes == False and query_yes_no("This will setup kernel remotes.\nDo you want to proceed?", 'no') is False:
        exit()

    profile = get_profile()
    if profile is None:
        exit("Failed to understand setup profile.")

    set_remotes(profile.setup["remotes"])
    git_remote_update()
    create_branches(profile.setup["branches"])
