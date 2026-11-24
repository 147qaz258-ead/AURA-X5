"""Deploy AURA-X5 firmware to live RDK X5 over SSH and light up 3.5" touchscreen.
Requires environment variables: RDK_HOST (default 192.168.128.10), RDK_USER (default root), RDK_PASS.
"""
import os
from pathlib import Path
import paramiko

HOST = os.environ.get("RDK_HOST", "192.168.128.10")
USER = os.environ.get("RDK_USER", "root")
PASS = os.environ.get("RDK_PASS")
ROOT = Path(__file__).resolve().parents[1]
FW_DIR = ROOT / "firmware"
REMOTE_DIR = "/opt/aura_x5"

FILES = [
    "ili9486_fast.c",
    "ili9486_spi.py",
    "display_ui.py",
    "hal_devices.py",
    "agent_core.py",
    "bpu_vision.py",
]

TEST_CMD = """
gcc -O2 -shared -fPIC /opt/aura_x5/ili9486_fast.c -o /opt/aura_x5/ili9486_fast.so
python3 - <<'PY'
import sys
sys.path.insert(0, '/opt/aura_x5')
from ili9486_spi import ILI9486ShiftSPI
from display_ui import UIState, render_ui_image
from hal_devices import XPT2046Touch

lcd = ILI9486ShiftSPI(spi_bus=1, spi_dev=0, max_hz=12000000)
state = UIState(
    connected_pc=True,
    privacy_mic_on=False,
    user_present=True,
    bpu_load_pct=12,
    proposal_title="AURA-X5 Connected!",
    proposal_summary="RDK X5 10-TOPS BPU Ready. Tap APPROVE or REJECT to test touch.",
    evidence_frame_id="boot-0001",
    status_banner="LIVE ON RDK X5",
)
img = render_ui_image(state)
lcd.push_rgb888(img)
print("LCD frame pushed successfully (480x320 RGB565).")

touch = XPT2046Touch(spi_bus=1, spi_dev=1)
raw = touch.read_raw()
print("XPT2046 raw sample:", raw)
PY
"""


def main():
    if not PASS:
        raise SystemExit("ERROR: Set RDK_PASS environment variable before deploying.")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, 22, USER, PASS, timeout=10)

    ssh.exec_command(f"mkdir -p {REMOTE_DIR}")
    sftp = ssh.open_sftp()
    for fname in FILES:
        local = FW_DIR / fname
        remote = f"{REMOTE_DIR}/{fname}"
        sftp.put(str(local), remote)
        print(f"Uploaded {fname} -> {remote}")
    sftp.close()

    _, stdout, stderr = ssh.exec_command(TEST_CMD)
    print(stdout.read().decode("utf-8", errors="replace"))
    err = stderr.read().decode("utf-8", errors="replace").strip()
    if err:
        print("STDERR:", err)
    ssh.close()


if __name__ == "__main__":
    main()
