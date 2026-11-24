"""Probe live D-Robotics RDK X5 hardware, buses, Python packages, and BPU models over SSH.
Configure via env vars: RDK_HOST, RDK_USER, RDK_PASS.
"""
import os
import paramiko

HOST = os.environ.get("RDK_HOST", "192.168.128.10")
USER = os.environ.get("RDK_USER", "root")
PASS = os.environ.get("RDK_PASS")

CMD = r"""
echo "=== UNAME ==="
uname -a
echo "=== DEVICES ==="
ls -l /dev/spidev* /dev/fb* /dev/i2c* /sys/class/udc /dev/hidg* 2>/dev/null || true
echo "=== PYTHON ==="
python3 - <<'PY'
import importlib.util as u
mods = ['Hobot.GPIO', 'hbm_runtime', 'spidev', 'PIL', 'numpy', 'cv2', 'websockets', 'fastapi', 'uvicorn', 'serial']
print({k: bool(u.find_spec(k)) for k in mods})
PY
echo "=== HBM MODELS ==="
find /app /opt /root -maxdepth 4 -name '*.hbm' 2>/dev/null | head -n 15
echo "=== USB GADGET ==="
ls /sys/kernel/config/usb_gadget 2>/dev/null || true
"""

def main():
    if not PASS:
        raise SystemExit("ERROR: Set RDK_PASS environment variable before probing.")
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, 22, USER, PASS, timeout=10)
    _, stdout, stderr = c.exec_command(CMD)
    print(stdout.read().decode("utf-8", errors="replace"))
    err = stderr.read().decode("utf-8", errors="replace").strip()
    if err:
        print("STDERR:", err)
    c.close()

if __name__ == "__main__":
    main()
