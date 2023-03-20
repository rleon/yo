"""YO cloud tools
"""
from utils.git import *
from utils.gerrit import *
from utils.cache import get_branch_cache
from utils.misc import get_project
from profiles import get_config
from texttable import Texttable
from datetime import datetime

import vendor.gerrit as gerrit

def print_branches_status(remote, branches, changeid):
    t = Texttable(max_width=0)
    t.set_header_align(["l", "c", "l", "l", "l", "l", "l", "l"])
    t.header(('Number', 'Subject', 'Branch', 'Updated', 'BT', 'CA', 'KC', 'RT'))

    host, port, project = get_gerrit_info(remote)
    rev = gerrit.Query(host, port)
    to_filter = [gerrit.OrFilter().add_items('change', changeid)]
    other = gerrit.Items()
    other.add_items('project', project)
    other.add_items('limit', len(changeid))

    to_filter.append(other)
    data = []
    for review in rev.filter(*to_filter):
        last_updated = datetime.fromtimestamp(review['lastUpdated'])
        last_updated = last_updated.strftime("%H:%M:%S %d-%m-%Y ")

        br = branches[changeid.index(review['id'])]
        approvals = review['currentPatchSet']['approvals']
        kc = ' '
        ca = ' '
        bt = ' '
        rt = ' '
        for d in approvals:
            if d['type'] == 'Kernel-Compile':
                kc = d['value']

            if d['type'] == 'Code-Analysis':
                ca = d['value']

            if d['type'] == 'Bluefield-Tests':
                bt = d['value']

            if d['type'] == 'Regression-Tests':
                rt = d['value']

        data.append((review['number'], br, review.get('branch'),
                     last_updated, bt, ca, kc, rt))

    t.add_rows(data, False)
    print(t.draw())

#--------------------------------------------------------------------------------------------------------
def args_verify(parser):
    parser.add_argument(
            "-n",
            "--dry-run",
            dest="dry_run",
            action="store_true",
            help="dry run",
            default=False)
    parser.add_argument(
            "-s",
            "--status",
            dest="status",
            action="store_true",
            help="Get regression status",
            default=False)
    parser.add_argument(
            "-v",
            "--verbose",
            dest="verbose",
            action="store_true",
            help="Be more verbose",
            default=False)

def cmd_verify(args):
    """Verify branches"""

    args.root = git_root()
    if args.root is None:
        exit()

    args.project = get_project(args)
    if args.project != "kernel":
        exit("Upload is supported for kernel tree only.")

    config = get_config("verify")
    remote = get_gerrit_remote()

    if not args.status:
        git_remote_update(remote)

    branches = config["branches"]

    base = []
    issue = []
    changeid = []
    for branch in branches:
        cache = get_branch_cache(branch)
        changeid += [cache['changeid']]
        if args.status:
            continue

        base += [git_find_base(remote, branch)]
        issue += [cache['issue']]

    if args.status:
        print_branches_status(remote, branches, changeid)
        return

    topic = [config["topic"]] * len(branches)
    git_push_squash_gerrit(remote, branches, base, branches, topic, issue,
                           changeid, args.dry_run, args.verbose)
