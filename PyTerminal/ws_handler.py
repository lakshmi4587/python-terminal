import asyncio
import websockets
import os
import subprocess
from main import handle_command as base_handle_command
from texteditor import editor_sessions, handle_edit_command, cmd_edit, cmd_write, handle_write_command

# ------------------------------
# Subprocess runner for `shell ...`
# ------------------------------
def run_shell_command(command: str) -> str:
    try:
        if os.name == "nt":  # Windows
            ps_cmd = f'powershell -Command "{command}"'
            result = subprocess.run(
                ps_cmd,
                capture_output=True,
                text=True,
                shell=True
            )
        else:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True
            )
        return result.stdout if result.returncode == 0 else result.stderr
    except Exception as e:
        return f"Error: {str(e)}"

# ------------------------------
# Main command handler
# ------------------------------
def handle_command(line: str) -> str:
    if line.startswith("shell "):
        cmd = line[len("shell "):].strip()
        return run_shell_command(cmd)
    return base_handle_command(line)

# ------------------------------
# Command history & autocomplete
# ------------------------------
session_history = {}

def add_to_history(session_id, cmd):
    hist = session_history.setdefault(session_id, [])
    hist.append(cmd)
    session_history[f"{session_id}_pointer"] = len(hist)

def get_history(session_id, direction):
    hist = session_history.setdefault(session_id, [])
    if not hist:
        return ""
    pointer = session_history.setdefault(f"{session_id}_pointer", len(hist))
    if direction == "up":
        pointer = max(0, pointer-1)
    else:  # down
        pointer = min(len(hist)-1, pointer+1)
    session_history[f"{session_id}_pointer"] = pointer
    return hist[pointer]

def autocomplete(prefix, session_id):
    from main import COMMANDS
    try:
        files = os.listdir(os.getcwd())
    except Exception:
        files = []
    options = list(COMMANDS.keys()) + files
    matches = [o for o in options if o.startswith(prefix)]
    return matches[0] if matches else prefix

# ------------------------------
# WebSocket handler
# ------------------------------
async def ws_handler(websocket):
    session_id = id(websocket)
    await websocket.send(f"{os.getcwd()}$ ")

    try:
        async for line in websocket:
            line = line.rstrip("\n\r")

            # --------------------------
            # Handle Up/Down arrows & Tab
            # --------------------------
            if line == "__UP__":
                prev_cmd = get_history(session_id, "up")
                if prev_cmd:
                    await websocket.send(prev_cmd)
                continue
            elif line == "__DOWN__":
                next_cmd = get_history(session_id, "down")
                if next_cmd:
                    await websocket.send(next_cmd)
                continue
            elif line.startswith("__TAB__"):
                prefix = line[len("__TAB__"):]
                suggestion = autocomplete(prefix, session_id)
                await websocket.send(suggestion)
                continue
            if line == "__CTRL_C__":
                # If inside editor
                if session_id in editor_sessions and editor_sessions[session_id]["active"]:
                    editor_sessions[session_id]["active"] = False
                    await websocket.send("^C\r\n(Edit cancelled)\r\n")
                else:
                    await websocket.send("^C\r\n")
                await websocket.send(f"{os.getcwd()}$ ")
                continue

            # --------------------------
            # Handle active editor/write sessions
            # --------------------------
            if session_id in editor_sessions and editor_sessions[session_id]["active"]:
                session = editor_sessions[session_id]
                if "append" in session:  # write session
                    result = handle_write_command(session_id, line)
                    if result:
                        await websocket.send(result + "\n")
                    if session["active"]:
                        await websocket.send("(write) > ")
                    else:
                        await websocket.send(f"{os.getcwd()}$ ")
                    continue
                else:  # edit session
                    result = handle_edit_command(session_id, line)
                    if result:
                        await websocket.send(result + "\n")
                    if session["active"]:
                        await websocket.send("(edit) > ")
                    else:
                        await websocket.send(f"{os.getcwd()}$ ")
                    continue

            # --------------------------
            # Empty input → reprint prompt
            # --------------------------
            if not line:
                await websocket.send(f"{os.getcwd()}$ ")
                continue

            # --------------------------
            # Start edit session
            # --------------------------
            if line.startswith("edit "):
                parts = line.split(maxsplit=1)
                args = parts[1:] if len(parts) > 1 else []
                result = cmd_edit(args, session_id=session_id)
                await websocket.send(result + "\n(edit) > ")
                continue

            # --------------------------
            # Start write session
            # --------------------------
            if line.startswith("write "):
                parts = line.split(maxsplit=1)
                args = parts[1:] if len(parts) > 1 else []
                result = cmd_write(args, session_id=session_id)
                await websocket.send(result + "\n(write) > ")
                continue

            # --------------------------
            # Normal commands
            # --------------------------
            output = await asyncio.to_thread(handle_command, line)
            add_to_history(session_id, line)

            if output in ("exit", "quit"):
                await websocket.send("Bye!\n")
                break

            if output:
                await websocket.send(output + "\n")

            await websocket.send(f"{os.getcwd()}$ ")

    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected.")

# ------------------------------
# Start WebSocket server
# ------------------------------
async def main():
    async with websockets.serve(ws_handler, "localhost", 8000):
        print("WebSocket server running at ws://localhost:8000")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
