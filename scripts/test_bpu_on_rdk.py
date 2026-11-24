"""Benchmark real 10-TOPS BPU inference on RDK X5 via hbm_runtime.
Configure via env vars: RDK_HOST, RDK_USER, RDK_PASS.
"""
import os
import paramiko

CMD = r"""
python3 - <<'PY'
import hbm_runtime, numpy as np, time
m = hbm_runtime.HB_HBMRuntime('/app/multimedia_samples/sunrise_camera/Platform/x5/model_zoom/mobilenetv2_224x224_nv12.bin')
mname = m.model_names[0]
iname = m.input_names[mname][0]
ishape = m.input_shapes[mname][iname]
print("Model:", mname, "Input:", iname, ishape)
dummy = {iname: np.zeros(ishape, dtype=np.uint8)}
t0 = time.time()
out = m.run(dummy)
dt = (time.time() - t0) * 1000.0
print("BPU_INFER_MS:", round(dt, 2), "Outputs:", {k: list(v.shape) for k, v in out[mname].items()})
PY
"""

HOST = os.environ.get("RDK_HOST", "192.168.128.10")
USER = os.environ.get("RDK_USER", "root")
PASS = os.environ.get("RDK_PASS")
if not PASS:
    raise SystemExit("ERROR: Set RDK_PASS environment variable before running SSH benchmark.")

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, 22, USER, PASS, timeout=10)
_, o, e = c.exec_command(CMD)
print(o.read().decode("utf-8", errors="replace"))
err = e.read().decode("utf-8", errors="replace").strip()
if err:
    print("STDERR:", err)
c.close()
