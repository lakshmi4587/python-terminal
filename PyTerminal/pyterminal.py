#!/usr/bin/env python3
"""
Python Terminal for Windows (Python 3.10+)
Features:
- File operations: ls, cd, pwd, mkdir, rm, rmdir, touch, cat, mv, cp, echo, write
- System info: ps, sysinfo
- Command history with timestamps (persistent)
- Tab completion (commands + files/folders)
Requires: psutil, prompt_toolkit
"""

import os
import sys
import shlex
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from prompt_toolkit.history import FileHistory
from shell_features import cmd_shell
from advanced_ls import cmd_ls_l
from process_mgmt import list_processes, kill_process, filter_process
from texteditor import cmd_edit,cmd_write  # your interactive editor
from nlp_handler import parse_nlp_command  # for NLP fallback if needed

# pyterminal.py
# from nlp_handler import parse_nlp_command

HISTORY_FILE = os.path.join(os.path.expanduser("~"), ".pyterminal_history")

WINDOWS_CMD_MAP = {
    "md": "mkdir",
    "del": "rm",
    "move": "mv",
    "copy": "cp",
}

# Optional: psutil for system info
try:
    import psutil
except ImportError:
    psutil = None

# Prompt toolkit for input with tab completion
try:
    from prompt_toolkit import prompt
    from prompt_toolkit.completion import WordCompleter
except ImportError:
    print("prompt_toolkit is required: pip install prompt_toolkit")
    sys.exit(1)

# --- History file for persistent timestamped commands ---
HISTORY_FILE = os.path.join(os.path.expanduser("~"), ".pyterminal_history")

# --- Utilities ---
def safe_print(s=""):
    try:
        print(s)
    except BrokenPipeError:
        sys.exit(0)

def abspath(path):
    return os.path.abspath(os.path.expanduser(path))

# --- Commands ---
def cmd_pwd(args):
    safe_print(os.getcwd())

def cmd_cd(args):
    target = args[0] if args else os.path.expanduser("~")
    try:
        os.chdir(abspath(target))
    except Exception as e:
        safe_print(f"cd: {e}")

def cmd_ls(args):
    path = args[0] if args else "."
    try:
        entries = sorted(os.listdir(abspath(path)))
        for e in entries:
            safe_print(e)
    except Exception as e:
        safe_print(f"ls: {e}")

def cmd_mkdir(args):
    if not args:
        safe_print("mkdir: missing operand")
        return
    for p in args:
        try:
            os.makedirs(abspath(p), exist_ok=False)
        except Exception as e:
            safe_print(f"mkdir: {e}")

def cmd_rm(args):
    if not args:
        safe_print("rm: missing operand")
        return
    for p in args:
        p_abs = abspath(p)
        try:
            if os.path.isdir(p_abs):
                shutil.rmtree(p_abs)
            else:
                os.remove(p_abs)
        except Exception as e:
            safe_print(f"rm: {e}")

def cmd_rmdir(args):
    if not args:
        safe_print("rmdir: missing operand")
        return
    for p in args:
        try:
            os.rmdir(abspath(p))
        except Exception as e:
            safe_print(f"rmdir: {e}")

def cmd_touch(args):
    if not args:
        safe_print("touch: missing file operand")
        return
    for p in args:
        p_abs = abspath(p)
        try:
            with open(p_abs, "a"):
                os.utime(p_abs, None)
        except Exception as e:
            safe_print(f"touch: {e}")

def cmd_cat(args):
    if not args:
        safe_print("cat: missing file operand")
        return
    for p in args:
        p_abs = abspath(p)
        try:
            with open(p_abs, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    safe_print(line.rstrip("\n"))
        except Exception as e:
            safe_print(f"cat: {e}")

def cmd_mv(args):
    if len(args) < 2:
        safe_print("mv: missing file operand")
        return
    srcs = args[:-1]
    dest = abspath(args[-1])
    try:
        if len(srcs) > 1 and not os.path.isdir(dest):
            safe_print("mv: target is not a directory")
            return
        for s in srcs:
            s_abs = abspath(s)
            shutil.move(s_abs, dest)
    except Exception as e:
        safe_print(f"mv: {e}")

def cmd_cp(args):
    if len(args) < 2:
        safe_print("cp: missing file operand")
        return
    srcs = args[:-1]
    dest = abspath(args[-1])
    try:
        if len(srcs) > 1 and not os.path.isdir(dest):
            safe_print("cp: target is not a directory")
            return
        for s in srcs:
            s_abs = abspath(s)
            if os.path.isdir(s_abs):
                shutil.copytree(s_abs, os.path.join(dest, os.path.basename(s_abs)))
            else:
                shutil.copy2(s_abs, dest)
    except Exception as e:
        safe_print(f"cp: {e}")

def cmd_echo(args):
    safe_print(" ".join(args))


def cmd_ps(args):
    if psutil is None:
        safe_print("ps: psutil not installed. Install with: pip install psutil")
        return
    try:
        for p in psutil.process_iter(["pid", "name", "username", "cpu_percent", "memory_percent"]):
            info = p.info
            safe_print(f"{info.get('pid'):>6} {info.get('name')[:25]:25} {info.get('username')[:12] if info.get('username') else '':12} CPU:{info.get('cpu_percent'):5.1f}% MEM:{info.get('memory_percent'):5.1f}%")
    except Exception as e:
        safe_print(f"ps: {e}")

def human_size(n):
    for unit in ["B","KB","MB","GB","TB"]:
        if n < 1024.0:
            return f"{n:3.1f}{unit}"
        n /= 1024.0
    return f"{n:.1f}PB"

def cmd_sysinfo():
    if psutil is None:
        safe_print("sysinfo: psutil not installed. Install with: pip install psutil")
        return
    try:
        cpu = psutil.cpu_percent(interval=0.3)
        mem = psutil.virtual_memory()
        safe_print(f"Time: {datetime.now().isoformat(sep=' ', timespec='seconds')}")
        safe_print(f"CPU Usage: {cpu}%")
        safe_print(f"Memory: {mem.percent}% used ({human_size(mem.used)} / {human_size(mem.total)})")
    except Exception as e:
        safe_print(f"sysinfo: {e}")

def cmd_history(args):
    """
    Show persistent command history with timestamps
    """
    if not os.path.exists(HISTORY_FILE):
        safe_print("No history found.")
        return
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            for line in f:
                safe_print(line.strip())
    except Exception as e:
        safe_print(f"history: {e}")


def cmd_help(args):
    safe_print("""Supported commands:
  ls [path]         - list files
  ls-l [path]       - detailed list with permissions, sizes (advanced_ls)
  cd [dir]          - change directory
  pwd               - print working directory
  mkdir <dir>       - create directory
  rm <file/dir>     - remove file or folder recursively
  rmdir <dir>       - remove an empty directory
  touch <file>      - create/update file timestamp
  cat <file>        - print file contents
  mv <src> <dst>    - rename
  cp <src> <dst>    - copy
  echo ...          - print args
  write [-a] <file> - write content to file, -a to append
  edit <file>       - interactive file editor (add/remove/modify lines)
  ps                - list processes (requires psutil)
  ps-list           - list processes (advanced features)
  ps-kill <pid>     - kill a process by PID
  ps-filter <args>  - filter processes by name/CPU/memory
  sysinfo           - cpu/memory summary (requires psutil)
  shell <command>   - run complex shell commands with pipes, redirects, globbing
  history           - show command history with timestamps
  help              - show this help
  exit / quit       - exit terminal
""")


# --- Command registry ---
COMMANDS = {
    "pwd": cmd_pwd,
    "cd": cmd_cd,
    "ls": cmd_ls,
    "ls-l": cmd_ls_l,
    "mkdir": cmd_mkdir,
    "rm": cmd_rm,
    "rmdir": cmd_rmdir,
    "touch": cmd_touch,
    "cat": cmd_cat,
    "mv": cmd_mv,
    "cp": cmd_cp,
    "echo": cmd_echo,
    "write": cmd_write,
    "edit": cmd_edit,
    "ps": cmd_ps,
    "ps-list": list_processes,
    "ps-kill": kill_process,
    "ps-filter": filter_process,
    "sysinfo": cmd_sysinfo,
    "history": cmd_history,
    "shell": cmd_shell,
    "help": cmd_help,
}



# # --- Tab completion using prompt_toolkit ---
# def get_completer():
#     try:
#         files = os.listdir(os.getcwd())
#     except Exception:
#         files = []
#     words = list(COMMANDS.keys()) + files
#     return WordCompleter(words, ignore_case=True)

# # --- Input with history (timestamped) ---
# def input_with_history(prompt_text):
#     completer = get_completer()
#     try:
#         # FileHistory enables Up/Down arrow navigation
#         line = prompt(prompt_text, completer=completer, history=FileHistory(HISTORY_FILE))

#         # Save timestamped command for `history` command
#         if line.strip():
#             with open(HISTORY_FILE, "a", encoding="utf-8") as f:
#                 f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {line}\n")
#         return line
#     except KeyboardInterrupt:
#         print()
#         return ""
#     except EOFError:
#         print()
#         sys.exit(0)



