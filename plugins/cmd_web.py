"""YO cloud tools
"""
from utils.git import *
from utils.gerrit import *

import vendor.gerrit as gerrit

#--------------------------------------------------------------------------------------------------------
def args_web(parser):
    parser.add_argument(
            "issue",
            nargs='?',
            help="Gerrit issue to open")
    parser.add_argument(
            "--results",
            dest="results",
            nargs='?',
            choices=['all', 'failed'],
            help="Get results links")
    parser.add_argument(
            "-v",
            "--verbose",
            dest="verbose",
            action="store_true",
            help="Be more verbose",
            default=False)

def cmd_web(args):
    """Open links"""

    args.root = git_root()
    if args.root is None:
        exit()

    if not args.issue:
        exit("Please provide gerrit issue")

    remote = get_gerrit_remote()
    host, port, project = get_gerrit_info(remote)
    rev = gerrit.Query(host, port)

    to_filter = []
    other = gerrit.Items()
    other.add_items('change', args.issue)
    other.add_items('limit', 1)
    if args.results:
        other.add_flags('comments')

    to_filter.append(other)

    for review in rev.filter(*to_filter):
        if not args.results:
            subprocess.call(['firefox', '-new-tab', '-url', review['url']])
            return

        matches = ['Code-Analysis-1', 'Kernel-Compile-1', 'Regression-Tests-1']
        if args.results == 'all':
            matches += ['Code-Analysis+1', 'Kernel-Compile+1', 'Regression-Tests+1']
        for comment in reversed(review['comments']):
            if comment['message'].startswith('Uploaded patch set '):
                break

            if any([x in comment['message'] for x in matches]):
                link = comment['message'].split()[-1]
                # We call to firefox on every call on purpose as it is only way
                # to open tab in existing firefox instance. If we provide list
                # of urls, it will open in new window instead.
                subprocess.call(['firefox', '-new-tab', '-url', link])
