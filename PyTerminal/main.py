# main.py
import os
import shlex
from pyterminal import *
from nlp_handler import parse_nlp_command
from shell_features import cmd_shell
from advanced_ls import cmd_ls_l
from process_mgmt import list_processes, kill_process, filter_process
from io import StringIO
import sys
import subprocess

# Commands that take zero arguments
ZERO_ARG_COMMANDS = ["ps-list", "sysinfo", "history"]

# Commands that take a single string argument
SINGLE_ARG_COMMANDS = ["ls-l", "pwd", "cat", "touch", "mkdir"]

# Commands that take a list of arguments
LIST_ARG_COMMANDS = ["rmdir", "rm", "echo", "cp", "mv"]

# ------------------------------
# Run shell command via subprocess (used for 'shell ...')
# ------------------------------
def run_shell_command(command: str) -> str:
    try:
        if os.name == "nt":  # Windows
            ps_cmd = f'powershell -Command "{command}"'
            result = subprocess.run(
                ps_cmd, capture_output=True, text=True, shell=True
            )
        else:  # Linux / macOS
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True
            )
        return result.stdout if result.returncode == 0 else result.stderr
    except Exception as e:
        return f"Error: {str(e)}"

# ------------------------------
# Main command handler
# ------------------------------
def handle_command(line: str) -> str:
    import sys
    from io import StringIO

    try:
        line = line.strip()
        if not line:
            return ""
        if line in ("exit", "quit"):
            return "exit"

        # Shell pipelines / redirects / wildcards
        if line.startswith("shell ") or any(c in line for c in "|><*?"):
            cmd = line[len("shell "):].strip() if line.startswith("shell ") else line
            return run_shell_command(cmd) if line.startswith("shell ") else cmd_shell(line)

        tokens = shlex.split(line)
        if not tokens:
            return ""

        cmd_name = tokens[0]
        args = tokens[1:]

        if cmd_name in COMMANDS:
            # Capture stdout into string
            old_stdout = sys.stdout
            sys.stdout = mystdout = StringIO()
            try:
                COMMANDS[cmd_name](args)  # pass full args list
            finally:
                sys.stdout = old_stdout
            return mystdout.getvalue()

        # NLP fallback
        nlp_cmd = parse_nlp_command(line)
        if nlp_cmd:
            return cmd_shell(nlp_cmd.strip().strip("`\"'"))

        return f"{cmd_name}: command not found"

    except Exception as e:
        return f"Error: {e}"
