"""YO cloud tools
"""
import sys
from utils.git import *
from utils.misc import *
from utils.cache import get_ai_cred

import warnings
warnings.filterwarnings("ignore", message="Core Pydantic V1 functionality isn't compatible")

from openai import OpenAI

def improve_message(args, client, message):
    completion = client.chat.completions.create(
            model = "azure/openai/gpt-5.1-chat",
            messages = [ { "role": "user",
                          "verbosity": "low",
                          "content" : "Improve english grammar, vocabulary and use \
                                  natuaral style as would write experienced linux kernel \
                                  developer with lines less than 80 characters, but \
                                  don't break links, functions and code snippets for \
                                  the following text: %s" %(message), },
                        ],
            )

    print(completion.choices[0].message.content)


#--------------------------------------------------------------------------------------------------------
def args_text(parser):
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

def cmd_text(args):
    """Perform AI tasks on texts"""

    if sys.stdin.isatty() is False:
        message = sys.stdin.read()
        message = f'"{message}"'
        # openai module adds annoying banner if input is piped
        sys.stdin.isatty = lambda: True  # or False, as needed
    else:
        args.root = git_root()
        if args.root is None:
            exit()

        args.project = get_project(args)
        if args.project != "kernel":
            exit("AI text is supported for kernel tree only.")

        git_call(["--no-pager", "log", "--oneline", "-n1", args.rev])
        message = git_simple_output(['log', '-1', args.rev, '--format="%B"'])

    url, key = get_ai_cred()
    client = OpenAI(base_url = url, api_key = key)
    improve_message(args, client, message)
