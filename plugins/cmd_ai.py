"""YO cloud tools
"""
from utils.git import *
from utils.misc import *
from utils.cache import get_ai_cred

import warnings
warnings.filterwarnings("ignore", message="Core Pydantic V1 functionality isn't compatible")

from openai import OpenAI

def commit_message(args, client):
    commit = git_simple_output(['log', '-1', args.rev, '--format="%B"'])
    completion = client.chat.completions.create(
            model = "azure/openai/gpt-5.1-chat",
            messages = [ { "role": "user",
                          "content" : "Improve english grammar, vocabulary and style \
                                  as would write experienced linux kernel developer \
                                  while keeping lines below 80 characters per-line \
                                  for the following commit message: %s" %(commit), },
                        ],
            )

    print(completion.choices[0].message.content)


#--------------------------------------------------------------------------------------------------------
def args_ai(parser):
    parser.add_argument(
            "rev",
            nargs='?',
            help="SHA1 to check",
            default = "HEAD")
    parser.add_argument(
            "-v",
            "--verbose",
            dest="verbose",
            action="store_true",
            help="Be more verbose",
            default=False)

def cmd_ai(args):
    """Attempt to perform AI tasks"""

    args.root = git_root()
    if args.root is None:
        exit()

    args.project = get_project(args)
    if args.project != "kernel":
        exit("Review is supported for kernel tree only.")

    git_call(["--no-pager", "log", "--oneline", "-n1", args.rev])
    url, key = get_ai_cred()
    client = OpenAI(base_url = url, api_key = key)

    commit_message(args, client)
