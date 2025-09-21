# nlp_handler.py

import subprocess

# Replace this with the name of the Ollama model installed on your laptop
MODEL_NAME = "llama3.2:latest"  # Example: "llama2" or your model name

def parse_nlp_command(nl_command: str) -> str:
    """
    Convert a natural language instruction into a shell command using Ollama.
    """
    if not nl_command.strip():
        return ""

    # Make the model output ONLY a command, no explanation, no markdown/backticks
    prompt = f"""
    You are a command translator for a custom shell called PyTerminal.

    Translate the following natural language instruction into ONE valid PyTerminal command.

    Rules:
    - Allowed commands: pwd, cd, ls, ls-l, mkdir, rm, rmdir, touch,
      cat, mv, cp, echo, write, edit, ps, ps-list, ps-kill, ps-filter,
      sysinfo, history, shell, help, sort, uniq, open
    - Use pipes (|) to chain commands if needed.
    - Do NOT use Linux-only flags (like -u, -l, etc.) unless they are in the allowed commands list.
    - For unique sorting, use: cat <file> | sort | uniq
    - For creating files inside folders, use: open <folder> create file <filename>
    - Output ONLY the command. No explanation, no extra text, no quotes, no backticks.

    Instruction: {nl_command}
    -for your reference these are the meanings of commands
    Supported commands:
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
"""

    try:
        result = subprocess.run(
            ["ollama", "run", MODEL_NAME, prompt],
            capture_output=True,
            text=True,
            encoding="utf-8",  # Fixes Windows Unicode errors
            errors="ignore"    # Skip any undecodable characters
        )

        # Clean the output: remove backticks, quotes, extra spaces, newlines
        command = result.stdout.strip().strip("`").strip('"').strip("'")

        # If the model returned empty, ignore
        if not command:
            return ""

        return command

    except FileNotFoundError:
        print("Error: Ollama CLI not found. Make sure Ollama is installed and added to PATH.")
        return ""
    except Exception as e:
        print(f"Error in NLP: {e}")
        return ""
