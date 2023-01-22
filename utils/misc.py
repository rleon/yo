import os
import subprocess
from contextlib import contextmanager

@contextmanager
def in_directory(dir):
    """Context manager that chdirs into a directory and restores the original
    directory when closed."""
    cdir = os.getcwd()
    try:
        os.chdir(dir)
        yield True
    finally:
        os.chdir(cdir)

project_marks = {
        "kernel": "scripts/faddr2line",
}

def get_project(args):
    """Look in the local folder to determine
    what we were requested to build"""

    # "custom" project can't be sensed and must be provided explicitly
    for key, value in project_marks.items():
        path = args.root + "/" + value
        if os.path.isfile(path):
            return key

    if not hasattr(args, "project"):
        exit("Failed to understand the source of this directory, Exiting...")

def fix_gpg_key():
    print("Refresh GPG key...")
    try:
        subprocess.check_call(["gpg", "--card-status"],
                              stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        subprocess.check_call(["sudo", "systemctl", "restart", "pcscd"])
        subprocess.check_call(["gpg", "--card-status"],
                              stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL)
