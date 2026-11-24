import os
import paramiko
CMD = r"""
python3 - <<'PY'
import Hobot.GPIO as G, os
G.setwarnings(False); G.setmode(G.BOARD); G.cleanup(); G.setmode(G.BOARD)
before = set(os.listdir("/sys/class/gpio"))
for p in (11, 18, 19, 21, 22, 23, 24, 26):
    G.setup(p, G.IN)
    now = set(os.listdir("/sys/class/gpio"))
    diff = now - before
    print(f"BOARD {p} -> {sorted(diff)}")
    before = now
G.cleanup()
PY
"""
HOST = os.environ.get("RDK_HOST", "192.168.128.10")
USER = os.environ.get("RDK_USER", "root")
PASS = os.environ.get("RDK_PASS")
if not PASS:
    raise SystemExit("ERROR: Set RDK_PASS environment variable before running SSH diagnostics.")
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, 22, USER, PASS, timeout=8)
_, o, e = c.exec_command(CMD)
print(o.read().decode(), e.read().decode())
c.close()
