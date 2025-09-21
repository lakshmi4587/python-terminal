import psutil


def list_processes():
    from pyterminal import safe_print
    """
    Display processes similar to top in a clean table.
    """
    header = f"{'PID':>6} {'NAME':25} {'CPU%':>6} {'MEM%':>6}"
    lines = [header]

    # first call to cpu_percent to initialize
    for p in psutil.process_iter(["pid", "name"]):
        p.cpu_percent(interval=None)

    # small sleep to get actual CPU%
    import time
    time.sleep(0.1)

    for p in psutil.process_iter(["pid","name","cpu_percent","memory_percent"]):
        info = p.info
        lines.append(
            f"{info['pid']:>6} {info['name'][:25]:25} "
            f"{info['cpu_percent']:6.1f} {info['memory_percent']:6.1f}"
        )

    safe_print("\n".join(lines))
def case_insensitive_match(sub, string):
    """
    Return True if sub is found in string, ignoring case.
    """
    if not sub or not string:
        return False
    sub_len = len(sub)
    for i in range(len(string) - sub_len + 1):
        match = True
        for j in range(sub_len):
            c1 = sub[j]
            c2 = string[i + j]
            # Convert uppercase ASCII letters to lowercase manually
            if 'A' <= c1 <= 'Z':
                c1 = chr(ord(c1) + 32)
            if 'A' <= c2 <= 'Z':
                c2 = chr(ord(c2) + 32)
            if c1 != c2:
                match = False
                break
        if match:
            return True
    return False

def kill_process(pid: int):
    """
    Kill a process by PID
    """
    from pyterminal import safe_print
    try:
        p = psutil.Process(pid)
        p.terminate()
        p.wait(timeout=3)
        safe_print(f"Process {pid} terminated.")
    except Exception as e:
        safe_print(f"kill: {e}")

def filter_process(name_substr: str):
    from pyterminal import safe_print
    import psutil

    header = f"{'PID':>6} {'NAME':25}"
    lines = [header]

    for p in psutil.process_iter(["pid", "name"]):
        pname = p.info.get("name")
        if pname and case_insensitive_match(name_substr, pname):
            lines.append(f"{p.info['pid']:>6} {pname[:25]}")

    safe_print("\n".join(lines))

