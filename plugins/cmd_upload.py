"""YO cloud tools
"""
from utils.cmdline import query_yes_no
from utils.git import *
from utils.misc import get_project, fix_gpg_key
from profiles import get_config

def upload_branches(upload, force=False, dry_run=False):
    for remote, branches in upload.items():
        b = [];
        for branch in branches:
            if git_same_content(branch[0], "%s/%s" % (remote, branch[1]), strict=True):
                continue

            b += [ "%s:%s" % (branch[0], branch[1])]

        if b:
            git_push(remote, b, force, dry_run)

#--------------------------------------------------------------------------------------------------------
def args_upload(parser):
    parser.add_argument(
            "-y",
            "--assume-yes",
            dest="yes",
            action="store_true",
            help="Automatically answer yes for all questions",
            default=False)
    parser.add_argument(
            "-n",
            "--dry-run",
            dest="dry_run",
            action="store_true",
            help="dry run",
            default=False)
    parser.add_argument(
            "--no-testing",
            dest="no_testing",
            action="store_true",
            help="Don't upload testing/* branches",
            default=False)

def cmd_upload(args):
    """Upload code"""

    args.root = git_root()
    if args.root is None:
        exit()

    args.project = get_project(args)
    if args.project != "kernel":
        exit("Upload is supported for kernel tree only.")

    config = get_config("upload")
    remotes = list(config["no_force"].keys()) + list(config["force"].keys())
    if not args.no_testing:
        remotes += list(config["cross_check"].keys())
        remotes += list(config["testing"].keys())

    remotes = list(set(remotes))

    git_remote_update(remotes)
    if not args.no_testing:
        # Let's hope for the best and this check will be valid
        # till we finish upload our branches
        for remote, branches in config["cross_check"].items():
            for branch in branches:
                safe_to_push = git_branch_contains(branch[0], "%s/%s" % (remote, branch[1]))

                if safe_to_push == False:
                    if args.yes == False:
                        print("Branch %s is newer than you have in %s." % (branch[1], branch[0]))

                        if query_yes_no("Do you want to proceed?", 'no') is False:
                            exit()

                    print("%s branch will use old %s" % (branch[0], branch[1]))


    fix_gpg_key()

    upload_branches(config["no_force"], force=False, dry_run=args.dry_run)
    upload_branches(config["force"], force=True, dry_run=args.dry_run)
    if not args.no_testing:
        upload_branches(config["testing"], force=True, dry_run=args.dry_run)
