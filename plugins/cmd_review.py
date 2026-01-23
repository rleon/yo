"""YO cloud tools
"""
import os
import sys
import json
import shutil
import tempfile
from utils.git import *
from utils.misc import *
from utils.cmdline import get_internal_fn

def print_result(stream, debug=False):
    """Extract plain text from Claude's stream-json format."""
    text_parts = []
    line_count = 0
    parsed_count = 0

    stream.seek(0)

    for line in stream:
        line_count += 1
        line = line.strip()

        if not line:
            continue

        if debug:
            print(f"Processing line {line_count}: {line[:100]}...", file=sys.stderr)

        try:
            data = json.loads(line)

            # Extract text from assistant messages
            if (data.get('type') == 'assistant' and
                'message' in data and
                'content' in data['message']):

                for content_item in data['message']['content']:
                    if content_item.get('type') == 'text':
                        text = content_item.get('text', '')
                        if text:
                            parsed_count += 1
                            text_parts.append(text)
                            if debug:
                                print(f"Extracted text {parsed_count}: {len(text)} chars", file=sys.stderr)

            # Handle streaming deltas (if Claude uses them)
            elif data.get('type') == 'content_block_delta':
                delta_text = data.get('delta', {}).get('text', '')
                if delta_text:
                    parsed_count += 1
                    text_parts.append(delta_text)
                    if debug:
                        print(f"Extracted delta {parsed_count}: {len(delta_text)} chars", file=sys.stderr)

        except json.JSONDecodeError as e:
            if debug:
                print(f"JSON decode error on line {line_count}: {e}", file=sys.stderr)
                print(f"Raw line: {line}", file=sys.stderr)
            continue
        except Exception as e:
            if debug:
                print(f"Unexpected error on line {line_count}: {e}", file=sys.stderr)
            continue

    if debug:
        print(f"Processed {line_count} lines, extracted {parsed_count} text parts, total {len(''.join(text_parts))} chars", file=sys.stderr)

    print(''.join(text_parts))

#--------------------------------------------------------------------------------------------------------
def args_review(parser):
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

def cmd_review(args):
    """Perform AI review"""

    args.root = git_root()
    if args.root is None:
        exit()

    args.project = get_project(args)
    if args.project != "kernel":
        exit("AI review is supported for kernel tree only.")

    git_call(["--no-pager", "log", "--oneline", "-n1", args.rev])

    with tempfile.TemporaryDirectory() as d:
        git_detach_workspace(d, args.verbose, args.rev)
        with in_directory(d):
            with tempfile.NamedTemporaryFile('w+') as f:
                prompt = "read prompt %s and run regression analysis of the top commit" %(get_internal_fn('../review-prompts/review-core.md'))
                cmd = ["claude", "-p", prompt,
                       "--mcp-config", '{"mcpServers":{"semcode":{"command":"semcode-mcp"}}}',
                       "--allowedTools", "mcp__semcode__find_function,\
                               mcp__semcode__diff_functions,\
                               mcp__semcode__grep_functions,\
                               mcp__semcode__find_callchain,\
                               mcp__semcode__find_callers,\
                               mcp__semcode__find_calls,\
                               mcp__semcode__find_type,\
                               mcp__semcode__find_commit",
                       "--model", "opus", "--verbose",
                       "--output-format=stream-json"]
                subprocess.run(cmd, stdout=f)
                print_result(f, debug=args.verbose)
                try:
                    shutil.copy("review-inline.txt", "%s/" %(args.root))
                except FileNotFoundError:
                    pass

    git_worktree_prune()
