"""YO cloud tools
"""
import sys
from utils.git import *
from utils.misc import *
from utils.cache import get_ai_cred

import warnings
warnings.filterwarnings("ignore", message="Core Pydantic V1 functionality isn't compatible")

from openai import OpenAI

def improve_message(args, client, message, note):
    completion = client.chat.completions.create(
            model = "azure/openai/gpt-5.1-chat",
            messages = [ { "role": "user",
                          "content" : "Improve english grammar, vocabulary and style \
                                  as would write experienced linux kernel developer \
                                  with lines less than 80 characters, but don't break \
                                  links, functions and code snippets for the following \
                                  %s: %s" %(note, message), },
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
    parser.add_argument(
            "-i",
            "--in-place",
            dest="in_place",
            action="store_true",
            help="Improve text in-place",
            default=False)

def cmd_ai(args):
    """Attempt to perform AI tasks"""

    args.root = git_root()
    if args.root is None:
        exit()

    if args.in_place:
        message = sys.stdin.read()
        note = "mail snippet"
    else:
        args.project = get_project(args)
        if args.project != "kernel":
            exit("Review is supported for kernel tree only.")

        git_call(["--no-pager", "log", "--oneline", "-n1", args.rev])
        message = git_simple_output(['log', '-1', args.rev, '--format="%B"'])
        note = "while keeping Linux kernel coding style for the following commit message"

    url, key = get_ai_cred()
    client = OpenAI(base_url = url, api_key = key)
    improve_message(args, client, message, note)
