import os
import tempfile
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

def switch_to_ssh(name, args=None, reconnect=False, clear=False):
    cmd = ['ssh', '-4', '-t', '-o', 'PreferredAuthentications=publickey',] + [name]
    if args is not None:
        cmd = cmd + args
    if not reconnect:
        os.execvp(cmd[0], cmd)

    with tempfile.NamedTemporaryFile("w") as f:
        cmd = ['until'] + cmd
        if clear:
            cmd += ['; do clear; echo "Keep trying to reconnect..."; sleep 10; done']
        else:
            cmd += ['; do echo "Keep trying to reconnect..."; sleep 10; done']
        f.write(' '.join(cmd))
        f.flush()

        cmd = ['sh', f.name]
        os.execvp(cmd[0], cmd)

def exec_on_remote(name, args=None, script=None):
    cmd = ['ssh', '-4', '-t', '-q', '-o', 'PreferredAuthentications=publickey',] + [name]
    if args is not None:
        cmd = cmd + args

    fstdin = None
    if script is not None:
        fstdin = script
    subprocess.run(cmd, stdin=fstdin)

def yo_root():
    return os.path.dirname((os.path.dirname(__file__) + ".."))
