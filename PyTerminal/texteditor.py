import os

# ------------------------------
# Editor sessions storage
# ------------------------------
editor_sessions = {}  # session_id -> session dict

def abspath(path):
    return os.path.abspath(os.path.expanduser(path))

# ------------------------------
# Edit command (existing)
# ------------------------------
def cmd_edit(args, session_id="local"):
    from pyterminal import safe_print

    if not args:
        safe_print("edit: missing filename")
        return "edit: missing filename"

    filename = abspath(args[0])
    lines = []

    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()

    editor_sessions[session_id] = {
        "type": "edit",
        "filename": filename,
        "lines": lines,
        "active": True
    }

    out = [f"Editing {filename}. Type ':help' for commands inside editor."]
    if lines:
        out.append("Current file content:")
        for i, line in enumerate(lines, 1):
            out.append(f"{i}: {line}")
    else:
        out.append("File is empty.")

    return "\n".join(out)


def handle_edit_command(session_id, cmd, input_line=None):
    from pyterminal import safe_print

    if session_id not in editor_sessions or not editor_sessions[session_id]["active"]:
        return "No active editor session. Use: edit <filename>"

    session = editor_sessions[session_id]
    filename = session["filename"]
    lines = session["lines"]

    if cmd == ":q":
        session["active"] = False
        return "Exiting editor without saving."

    elif cmd == ":w":
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
            return f"{filename} saved successfully."
        except Exception as e:
            return f"edit: {e}"

    elif cmd == ":p":
        if lines:
            return "\n".join(f"{i}: {line}" for i, line in enumerate(lines, 1))
        else:
            return "File is empty."

    elif cmd.startswith(":d "):
        try:
            n = int(cmd.split()[1])
            if 1 <= n <= len(lines):
                removed = lines.pop(n - 1)
                return f"Deleted line {n}: {removed}"
            else:
                return "Invalid line number"
        except:
            return "Usage: :d <line_number>"

    elif cmd.startswith(":i ") or cmd.startswith(":r "):
        parts = cmd.split(maxsplit=2)
        if len(parts) < 3:
            return "Insert/Replace text missing."
        n = int(parts[1])
        input_line = parts[2]

        if cmd.startswith(":i "):
            if 1 <= n <= len(lines)+1:
                lines.insert(n-1, input_line)
                return f"Inserted at line {n}"
            else:
                return "Invalid line number"
        else:  # :r
            if 1 <= n <= len(lines):
                lines[n-1] = input_line
                return f"Replaced line {n}"
            else:
                return "Invalid line number"

    elif cmd == ":help":
        return """Editor commands:
  :q        -> quit without saving
  :w        -> save changes
  :p        -> print current content
  :d <n>    -> delete line n
  :i <n>    -> insert a line before n (needs text)
  :r <n>    -> replace line n (needs text)
"""

    else:
        return "Unknown editor command. Type ':help' for commands."

# ------------------------------
# Write command (non-blocking, WebSocket-friendly)
# ------------------------------
def cmd_write(args, session_id=None):
    """
    Start a write session.
    Usage:
        write filename.txt         # overwrite
        write -a filename.txt      # append
    End input with a single '.' on a line.
    """
    if not args:
        return "write: missing filename"

    append = False
    if args[0] == "-a":
        append = True
        if len(args) < 2:
            return "write: missing filename"
        filename = abspath(args[1])
    else:
        filename = abspath(args[0])

    editor_sessions[session_id] = {
        "type": "write",
        "active": True,
        "buffer": [],
        "filename": filename,
        "append": append
    }

    return f"{'Appending to' if append else 'Writing to'} {filename}. End with a single '.' on a line."

def handle_write_command(session_id, line):
    """
    Handle a line typed in a write session.
    """
    session = editor_sessions[session_id]

    if line.strip() == ".":
        # Save file
        mode = "a" if session.get("append") else "w"
        try:
            with open(session["filename"], mode, encoding="utf-8") as f:
                if session.get("append") and os.path.getsize(session["filename"]) > 0:
                    f.write("\n")
                f.write("\n".join(session["buffer"]) + "\n")
        except Exception as e:
            session["active"] = False
            return f"write: {e}"

        session["active"] = False
        return f"{session['filename']} saved successfully."

    # Otherwise append line to buffer
    session["buffer"].append(line)
    return ""  # no output yet
