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

def print_patches_status(remote, changeid):
    t = Texttable(max_width=0)
    t.set_header_align(["l", "l", "l", "l", "l", "l", "l"])
    t.header(('Issue', 'Subject', 'Updated', 'BT', 'CA', 'KC', 'RT'))

    host, port, project = get_gerrit_info(remote)
    rev = gerrit.Query(host, port)
    to_filter = [gerrit.OrFilter().add_items('change', changeid)]
    other = gerrit.Items()
    other.add_items('project', project)
    other.add_items('limit', len(changeid))

    to_filter.append(other)
    data = [None] * len(changeid)
    for review in rev.filter(*to_filter):
        last_updated = datetime.fromtimestamp(review['lastUpdated'])
        last_updated = last_updated.strftime("%H:%M:%S %d-%m-%Y ")

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

        idx = changeid.index(review.get('id'))
        data[idx] = ((review['number'], review.get('subject'), last_updated, bt, ca, kc, rt))

    t.add_rows(data, False)
    print(t.draw())

#--------------------------------------------------------------------------------------------------------
def args_status(parser):
    pass

def cmd_status(args):
    """Patches status"""

    args.root = git_root()
    if args.root is None:
        exit()

    args.project = get_project(args)
    if args.project != "kernel":
        exit("Upload is supported for kernel tree only.")

    remote = get_gerrit_remote()
    log = git_simple_output(["log", "-50"])
    changeid = []
    for line in log.splitlines():
        if "Change-Id" in line:
            line = line.split(':')
            changeid += [line[1].strip()]

    if not changeid:
        exit("No patches found in the current branch.")

    print_patches_status(remote, changeid)
