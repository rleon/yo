"""YO cloud tools
"""
import os
import shutil
import tempfile
from utils.git import *
from utils.misc import *

def is_b4_tracked(args):
    branch = git_current_branch().strip()
    if not branch.startswith("b4/"):
        return False

    return True

B4_BIN = os.path.expanduser("~/src/b4/b4.sh")

def create_b4_mbox(args):
    """Create an mbox file from the series on the current b4 prep branch.

    Mirrors the ``git patch`` alias in ~/.gitaliases: asks ``b4 prep`` for the
    current revision, then uses ``b4 send -o`` to emit each message of the
    series as a standalone file (already in mboxrd ``From ``-prefixed form)
    and concatenates them into a single mbox.  Stores the path in
    ``args.b4_mbox``.
    """
    rev_out = subprocess.check_output(
        [B4_BIN, "prep", "--show-revision"],
        stderr=subprocess.STDOUT,
    ).decode().splitlines()
    revision = rev_out[0].strip() if rev_out else "v1"

    out_dir = tempfile.mkdtemp(prefix="b4-send-")
    if args.verbose:
        subprocess.check_call([B4_BIN, "send", "--not-me-too", "-o", out_dir])
    else:
        subprocess.check_call(
            [B4_BIN, "send", "--not-me-too", "-o", out_dir],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    # b4 send -o writes bare .eml files with no mbox "From " separator, so
    # concatenating them would look like a single giant message to any mbox
    # splitter (e.g. sashiko's, which keys off "From ... HH:MM:SS" lines).
    # Prepend a synthetic From_ line before each message to form valid mboxrd.
    mbox_fd, mbox_path = tempfile.mkstemp(prefix="b4-series-", suffix=".mbox")
    with os.fdopen(mbox_fd, "wb") as mbox:
        for name in sorted(os.listdir(out_dir)):
            mbox.write(b"From b4 Thu Jan  1 00:00:00 1970\n")
            with open(os.path.join(out_dir, name), "rb") as f:
                content = f.read()
            mbox.write(content)
            if not content.endswith(b"\n"):
                mbox.write(b"\n")

    shutil.rmtree(out_dir, ignore_errors=True)
    args.mbox = mbox_path

    # Locate b4's cover-letter commit (marked with the b4-submit-tracking
    # magic line in its message) and record the SHA of its parent — i.e. the
    # commit right before the cover letter on the b4 branch.
    cover = git_simple_output([
        "log", "--grep=--- b4-submit-tracking ---", "-F",
        "--pretty=%H", "--max-count=1", "HEAD",
    ])
    if not cover:
        exit("Could not locate b4 cover-letter commit on current branch")
    args.base = git_simple_output(["rev-parse", "%s~1" % cover])

SASHIKO_NBU_URL = "http://sashiko-nbu.nvidia.com"
SASHIKO_CLI = "/home/leonro/src/sashiko/target/release/sashiko-cli"

def submit_to_sashiko(args):
    """Submit the mbox at ``args.mbox`` to sashiko-nbu via the sashiko-cli.

    Delegates to ``sashiko-cli submit --type mbox --baseline <sha>``
    pointed at the NBU server.  Returns the CLI's stdout as a string.
    """
    cmd = [
        SASHIKO_CLI,
        "--server", SASHIKO_NBU_URL,
        "submit",
        "--baseline", args.base,
    ]
    with open(args.mbox, "rb") as fh:
        out = subprocess.check_output(cmd, stdin=fh).decode()
    print(out, end="")
    return out

#--------------------------------------------------------------------------------------------------------
def args_review(parser):
    parser.add_argument(
            "-v",
            "--verbose",
            dest="verbose",
            action="store_true",
            help="Be more verbose",
            default=False)

def cmd_review(args):
    """Perform AI review"""

    args.root = git_root()
    if args.root is None:
        exit()

    args.project = get_project(args)
    if args.project != "kernel":
        exit("AI review is supported for kernel tree only.")

    args.mbox = None
    if is_b4_tracked(args):
        create_b4_mbox(args)
    else:
        exit("Supported for local b4 tracked branches")

    print(args.base)
    submit_to_sashiko(args)
