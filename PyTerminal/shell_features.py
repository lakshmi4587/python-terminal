import shlex
import glob
import os
import subprocess

# --- Expand wildcards like * and ? ---
def expand_globs(tokens):
    expanded_tokens = []
    for t in tokens:
        if "*" in t or "?" in t:
            matches = glob.glob(t)
            if matches:
                expanded_tokens.extend(matches)
            else:
                expanded_tokens.append(t)
        else:
            expanded_tokens.append(t)
    return expanded_tokens

# --- Builtin commands ---
def builtin_cat(args, input_lines=None):
    from pyterminal import safe_print
    lines = input_lines if input_lines else []
    if not input_lines:
        for filename in args:
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    lines.extend(f.read().splitlines())
            except Exception as e:
                safe_print(f"cat: {e}")
    return lines

def builtin_sort(args, input_lines=None):
    from pyterminal import safe_print
    lines = []

    if input_lines:
        lines = input_lines[:]   # use piped input
    elif args:                  # otherwise read files
        for filename in args:
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    lines.extend(f.read().splitlines())
            except Exception as e:
                safe_print(f"sort: {e}")

    lines.sort()
    return lines

def builtin_uniq(args, input_lines=None):
    from pyterminal import safe_print
    lines = input_lines if input_lines else []
    if not lines and args:
        for filename in args:
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    lines.extend(f.read().splitlines())
            except Exception as e:
                safe_print(f"uniq: {e}")
    uniq_lines = []
    prev = None
    for line in lines:
        if line != prev:
            uniq_lines.append(line)
            prev = line
    return uniq_lines

# Map built-in command names to functions
BUILTINS = {
    "cat": builtin_cat,
    "sort": builtin_sort,
    "uniq": builtin_uniq,
}

# --- Pipeline runner (hybrid: builtins + subprocess) ---
def run_pipeline(pipe_parts):
    from pyterminal import COMMANDS
    from pyterminal import safe_print

    prev_output = None

    for part in pipe_parts:
        tokens = shlex.split(part)
        tokens = expand_globs(tokens)
        if not tokens:
            continue

        cmd_name, cmd_args = tokens[0], tokens[1:]

        # 1️⃣ If it's one of your custom commands
        if cmd_name in COMMANDS:
            try:
                func = COMMANDS[cmd_name]
                output = func(cmd_args)   # run your Python terminal command
                if isinstance(output, list):
                    prev_output = "\n".join(output)
                elif output is not None:
                    prev_output = str(output)
            except Exception as e:
                safe_print(f"{cmd_name}: {e}")

        # 2️⃣ Else if it's one of your builtins
        elif cmd_name in BUILTINS:
            input_lines = prev_output.splitlines() if prev_output else None
            output_lines = BUILTINS[cmd_name](cmd_args, input_lines)
            prev_output = "\n".join(output_lines)

        # 3️⃣ Otherwise, fallback to system command
        else:
            proc = subprocess.Popen(
                tokens,
                stdin=subprocess.PIPE if prev_output else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            out, err = proc.communicate(input=prev_output if prev_output else None)
            if err:
                safe_print(err)
            prev_output = out

    return prev_output.splitlines() if prev_output else []

# --- Main shell executor ---
def cmd_shell(command_line: str):
    from pyterminal import safe_print
    """
    Execute a shell-like command line supporting:
    - Multiple commands (&& ;)
    - Pipes (|)
    - Redirects (> >>)
    - Globbing (* ?)
    - Built-in commands entirely in Python
    """
    if not command_line.strip():
        return

    # --- Handle multiple commands separated by && or ; ---
    if "&&" in command_line or ";" in command_line:
        separators = ["&&", ";"]
        for sep in separators:
            if sep in command_line:
                parts = [p.strip() for p in command_line.split(sep) if p.strip()]
                for part in parts:
                    cmd_shell(part)  # recursively execute each command
                return  # stop here (already executed sub-commands)

    # --- Check for output redirection ---
    output_file = None
    mode = None
    if ">>" in command_line:
        parts = command_line.rsplit(">>", 1)
        command_line = parts[0].strip()
        output_file = parts[1].strip()
        mode = "a"
    elif ">" in command_line:
        parts = command_line.rsplit(">", 1)
        command_line = parts[0].strip()
        output_file = parts[1].strip()
        mode = "w"

    # --- Handle pipelines (|) ---
    pipe_parts = [p.strip() for p in command_line.split("|")]
    input_lines = run_pipeline(pipe_parts)

    # --- Output handling ---
    if input_lines:
        if output_file:
            try:
                with open(output_file, mode, encoding="utf-8") as f:
                    f.write("\n".join(input_lines) + "\n")
                safe_print(f"Output redirected to {output_file}")
            except Exception as e:
                safe_print(f"Redirection error: {e}")
        else:
            for line in input_lines:
                safe_print(line)
