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

def recheck_patches(remote, changeid, issue, recheck, recheck_debug):
    host, port, project = get_gerrit_info(remote)
    rev = gerrit.Query(host, port)
    if not changeid:
        to_filter = [gerrit.OrFilter().add_items('change', issue)]
    else:
        to_filter = [gerrit.OrFilter().add_items('change', changeid)]
    other = gerrit.Items()
    other.add_items('project', project)
    if not changeid:
        other.add_items('limit', 1)
        data = [None]
    else:
        other.add_items('limit', len(changeid))
        data = [None] * len(changeid)

    to_filter.append(other)
    for review in rev.filter(*to_filter):
        try:
            review['type']
            exit("No patches found in the current branch.")
        except KeyError:
            pass

        r = gerrit.Review("%s,%s" %(review.get('number'), review.get('currentPatchSet').get('number')),
                          host, port)
        if recheck:
            r.commit("jenkins_recheck")
        if recheck_debug:
            r.commit("jenkins_recheck_dbg")

def print_patches_status(remote, changeid, issue):
    t = Texttable(max_width=0)
    t.set_header_align(["l", "l", "l", "l", "l", "l", "l"])
    t.header(('Issue', 'Subject', 'Updated', 'BT', 'CA', 'KC', 'RT'))

    host, port, project = get_gerrit_info(remote)
    rev = gerrit.Query(host, port)
    if not changeid:
        to_filter = [gerrit.OrFilter().add_items('change', issue)]
    else:
        to_filter = [gerrit.OrFilter().add_items('change', changeid)]
    other = gerrit.Items()
    other.add_items('project', project)
    if not changeid:
        other.add_items('limit', 1)
        data = [None]
    else:
        other.add_items('limit', len(changeid))
        data = [None] * len(changeid)

    to_filter.append(other)
    for review in rev.filter(*to_filter):
        try:
            review['type']
            exit("No patches found in the current branch.")
        except KeyError:
            pass

        last_updated = datetime.fromtimestamp(review['lastUpdated'])
        last_updated = last_updated.strftime("%H:%M:%S %d-%m-%Y ")

        kc = ' '
        ca = ' '
        bt = ' '
        rt = ' '
        try:
            approvals = review['currentPatchSet']['approvals']
            for d in approvals:
                if d['type'] == 'Kernel-Compile':
                    kc = d['value']

                if d['type'] == 'Code-Analysis':
                    ca = d['value']

                if d['type'] == 'Bluefield-Tests':
                    bt = d['value']

                if d['type'] == 'Regression-Tests':
                    rt = d['value']
        except KeyError:
            pass

        if not changeid:
            idx = 0
        else:
            idx = changeid.index(review.get('id'))
        data[idx] = ((review['number'], review.get('subject'), last_updated, bt, ca, kc, rt))

    data = list(filter(None, data))
    t.add_rows(data, False)
    print(t.draw())

#--------------------------------------------------------------------------------------------------------
def args_status(parser):
    parser.add_argument(
            "issue",
            nargs='?',
            help="Gerrit issue or SHA1 to check status")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
            "--recheck",
            dest="recheck",
            action="store_true",
            help="Rerun CI checks",
            default=False)
    group.add_argument(
            "--recheck-debug",
            dest="recheck_debug",
            action="store_true",
            help="Rerun CI verbose checks",
            default=False)

def cmd_status(args):
    """Patches status"""

    args.root = git_root()
    if args.root is None:
        exit()

    args.project = get_project(args)
    if args.project != "kernel":
        exit("Upload is supported for kernel tree only.")

    remote = get_gerrit_remote()
    changeid = []
    log = None
    is_issue_sha = False
    if args.issue:
        is_issue_sha = git_commit_exists(args.issue)
        if is_issue_sha:
            log = git_simple_output(["log", "-q", "-1", args.issue])
    else:
        log = git_simple_output(["log", "-50"])

    if log is not None:
        for line in log.splitlines():
            if "Change-Id" in line:
                line = line.split(':')
                changeid += [line[1].strip()]

    if not changeid and not args.issue:
        exit("No patches found in the current branch.")

    if args.recheck or args.recheck_debug:
        recheck_patches(remote, changeid, args.issue, args.recheck, args.recheck_debug)
        return

    print_patches_status(remote, changeid, args.issue)
