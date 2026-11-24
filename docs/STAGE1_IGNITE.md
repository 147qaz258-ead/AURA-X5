# Stage 1 — Ignite Challenge Report (AURA-X5)

> **Official Requirement:** [`stages/stage1-ignite.md`](https://github.com/D-Robotics/Robotics-Dream-Keeper-Challenge-Winter/blob/main/stages/stage1-ignite.md)  
> **Hardware Baseline:** D-Robotics RDK X5 (Linux 6.1.83, `hbm_runtime 1.24.5` / HBRT `3.15.55.0`)  
> **Evidence Folder:** `docs/evidence/stage1/`

---

## 1. Challenge 1 — Board Bring-Up (Flash, Network & SSH)

### Setup Steps Executed
1. Flashed the official D-Robotics RDK X5 Ubuntu 22.04 OS image via **RDK Studio**.
2. Connected RDK X5 over Ethernet / USB network (`RDK_HOST=192.168.128.10`) and verified internet reachability.
3. Verified SSH login and probed hardware buses (`spidev`, `i2c`, `udc`, Python runtimes, and pre-installed BPU `.bin`/`.hbm` models) via [`scripts/rdk_probe.py`](../scripts/rdk_probe.py):

```bash
export RDK_HOST="192.168.128.10"
export RDK_USER="root"
export RDK_PASS="<your-password>"
python3 scripts/rdk_probe.py
```

### Required Evidence (Replace placeholders with actual screenshots before submitting PR)
- [ ] `docs/evidence/stage1/01_flash_and_ssh.png` — Composite screenshot showing RDK Studio flash confirmation + active SSH terminal (`uname -a`, `ip a`, `ls /dev/spidev* /dev/i2c*`).  
  *(Security check: mask Wi-Fi passwords, private keys, tokens, and serial numbers.)*

---

## 2. Challenge 2 — Sensor / Peripheral Explorer

AURA-X5 exercises multiple RDK X5 hardware interfaces defined in [`interfaces.json`](../interfaces.json):
- **SPI + GPIO (`spidev1.0`, GPIO Pins 11/18/19/21/22/23/24/26)**: 3.5" 480×320 ILI9486 LCD + XPT2046 resistive touch controller (`firmware/ili9486_spi.py`, `firmware/hal_devices.py`, deployed via `scripts/deploy_to_rdk.py`).
- **40-Pin GPIO (`Hobot.GPIO`, BOARD mode)**: EC11 rotary encoder (Pins 13/15/16), Emergency Kill-Switch (Pin 7), DPDT Hardware Privacy Sense (Pin 29), PWM Cooling Fan (Pin 32).
- **UART (`/dev/ttyS1`, 256000 baud, Pins 8/10)**: HLK-LD2410C 24 GHz mmWave human presence radar (`parse_ld2410c_frame()` verified by unit tests).
- **I2C (`i2c-5`, Pins 3/5)**: Probed via `firmware/sensor_hub.py` for VL53L1X (`0x29`), INA219 (`0x40`), SHT40 (`0x44`).

### Reproduction Command (3.5" SPI Display & Touch Bring-up)
```bash
python3 scripts/deploy_to_rdk.py
```
Expected log:
```text
LCD frame pushed successfully (480x320 RGB565).
XPT2046 raw sample: (<x>, <y>, <z>)
```

### Required Evidence
- [ ] `docs/evidence/stage1/02_sensor_peripheral.jpg` (or short `.mp4` / link) — Photo or short clip showing live RDK X5 driving the display/touch or reading GPIO/radar/sensor output with interface labeled.

---

## 3. Challenge 3 — First On-Device AI Task (BPU)

Ran on-device image classification directly on the RDK X5 **10 TOPS Bayes BPU** using `hbm_runtime.HB_HBMRuntime` with the compiled quantized model:
- **Model:** `mobilenetv2_224x224_nv12.bin` (`/app/multimedia_samples/sunrise_camera/Platform/x5/model_zoom/mobilenetv2_224x224_nv12.bin`)
- **Runtime:** `hbm_runtime 1.24.5` (HBRT `3.15.55.0`)
- **Script:** [`scripts/test_bpu_on_rdk.py`](../scripts/test_bpu_on_rdk.py) and [`firmware/bpu_vision.py`](../firmware/bpu_vision.py)

### Reproduction Command
```bash
python3 scripts/test_bpu_on_rdk.py
```
Sample terminal verification output format:
```text
Model: mobilenetv2_224x224_nv12 Input: ... [1, 3, 224, 224]
BPU_INFER_MS: <measured_ms> Outputs: {...}
```

### Required Evidence
- [ ] `docs/evidence/stage1/03_first_ai_bpu.png` — Screenshot of the live SSH terminal / visual output showing our own RDK X5 running the BPU model.

---

## 4. Stage 1 Deliverables Checklist

| # | Deliverable | Status | Location / Link |
|---|---|---|---|
| 1 | Flash + SSH screenshot | Pending capture | `docs/evidence/stage1/01_flash_and_ssh.png` |
| 2 | Sensor / peripheral photo or clip | Pending capture | `docs/evidence/stage1/02_sensor_peripheral.jpg` |
| 3 | On-device AI task screenshot | Pending capture | `docs/evidence/stage1/03_first_ai_bpu.png` |
| 4 | Personal GitHub repo README | Ready | [`README.md`](../README.md) |
| 5 | Discord Stage 1 check-in link | Pending post | `<paste-discord-permalink>` |
| 6 | Official Showcase PR | Draft ready | [`showcase_pr/ParticipantName-Project-AURA-X5.md`](../showcase_pr/ParticipantName-Project-AURA-X5.md) |
