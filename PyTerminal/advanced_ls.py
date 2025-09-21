import os
import stat
from datetime import datetime


def cmd_ls_l(path="."):
    from pyterminal import safe_print
    """
    Print detailed listing like `ls -l`:
    Permissions, owner, size, modification time.
    Can show a directory or a single file.
    """
    path = os.path.abspath(os.path.expanduser(path))

    try:
        # If it's a directory, list all entries
        if os.path.isdir(path):
            entries = sorted(os.listdir(path))
            for e in entries:
                full_path = os.path.join(path, e)
                st = os.stat(full_path)
                perms = stat.filemode(st.st_mode)
                size = st.st_size
                mtime = datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M")
                safe_print(f"{perms} {size:>10} {mtime} {e}")

        # If it's a single file, show only that
        elif os.path.isfile(path):
            st = os.stat(path)
            perms = stat.filemode(st.st_mode)
            size = st.st_size
            mtime = datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M")
            fname = os.path.basename(path)
            safe_print(f"{perms} {size:>10} {mtime} {fname}")

        else:
            safe_print(f"ls-l: cannot access '{path}': No such file or directory")

    except Exception as e:
        safe_print(f"ls-l error: {e}")
