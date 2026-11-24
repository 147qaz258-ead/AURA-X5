# Stage 2 — Engineering Plan (BOM, Schedule, Risks & Repository Structure)

> **Official Requirement:** [`stages/stage2-build.md` — Challenge 3](https://github.com/D-Robotics/Robotics-Dream-Keeper-Challenge-Winter/blob/main/stages/stage2-build.md)  
> **Hardware BOM Sources:** [`electronics/bom.csv`](../electronics/bom.csv) · [`electronics/bom_easyeda_native.csv`](../electronics/bom_easyeda_native.csv)  
> **PCB DRC Proof:** [`electronics/validation.json`](../electronics/validation.json) (`0` DRC errors, `0` unconnected nets)  
> **3D Enclosure Proof:** [`mechanical/fit_check.json`](../mechanical/fit_check.json) (3/3 STL parts watertight)

---

## 1. Bill of Materials (BOM)

AURA-X5 supports **two build tiers** on the exact same RDK X5 firmware & ROS 2 stack:
- **Core System + V2 Solderless HDMI Edition** (zero soldering, DuPont wires straight to the 40-pin header).
- **V1 Custom Carrier HAT (`aura_x5_hat`) + 3.5" SPI Touch + 3D Printed Enclosure** (full manufacturing pack in `electronics/` & `mechanical/`).

### 1.1 Core Compute, Display & Panel Controls

| Category | Item Name | Qty | Supplier / SKU / MPN | Voltage & Interface | Est. Cost (USD) | Notes |
|---|---|---|---|---|---|---|
| Compute | **D-Robotics RDK X5** (10 TOPS BPU, 4GB/8GB) | 1 | D-Robotics Official | `5V / 5A` USB-C PD; 40-Pin 3.3V GPIO; USB-C OTG | \$75.00 | Required baseline |
| Storage | Industrial microSD Card (64 GB, A2/U3) | 1 | SanDisk / Samsung | 3.3V SDIO | \$8.00 | Official RDK OS Ubuntu 22.04 |
| Display (V2) | HDMI External Secondary Display (5"–7" or Desktop Monitor) | 1 | Generic HDMI 1080p/800×480 | `5V` USB + Micro/Standard HDMI | \$25.00 | V2 60 FPS Chromium Kiosk UI |
| Display (V1) | 3.5" 480×320 TFT Touch Display (ILI9486 + XPT2046) | 1 | MPI3501 / Generic RPi 26-Pin | `5V` (~130 mA), SPI (`spidev1.0`) + GPIO | \$12.00 | V1 compact console option |
| Safety I/O | 6-Pin DPDT Hardware Privacy Toggle Switch | 1 | Standard DPDT 6P | `3.3V` rail cut (`V_PRIVACY_3V3`) + GPIO Pin 29 | \$0.80 | Hard-cuts mic/cam power |
| Safety I/O | 12 mm Momentary Push Button (Kill-Switch) | 1 | 2P Normally-Open | `3.3V` GPIO Pin 7 (active-low to GND Pin 9) | \$0.60 | Hardware emergency stop |
| User I/O | EC11 Rotary Encoder with Push Switch | 1 | Standard EC11 5-Pin | `3.3V` GPIO Pins 13/15/16 (A/B/SW) | \$0.90 | Scroll & physical approve |
| Cooling | 30×30×7 mm 5V Cooling Fan | 1 | Generic 5V 2-Wire | `5V` (direct or NPN PWM on GPIO Pin 32) | \$2.00 | Keeps BPU < 75 °C |
| Cables | USB-C High-Speed Data Cable + 40-Pin DuPont Jumper Set | 1 set | Generic | USB 2.0 OTG (`ecm.usb0` + `hidg0/1`) | \$4.00 | Single-cable PC link |

### 1.2 Optional / Modular Sensors & Actuators

| Category | Item Name | Qty | Supplier / SKU / MPN | Voltage & Interface | Est. Cost (USD) | Notes |
|---|---|---|---|---|---|---|
| Radar | HLK-LD2410C 24 GHz mmWave Presence Radar | 1 | Hi-Link `HLK-LD2410C` | `5V`, UART `/dev/ttyS1` (256000 baud, Pins 8/10) | \$3.50 | Desk human presence |
| Env Sensor | SHT40 Digital Temp & Humidity Sensor | 1 | Sensirion `SHT40` | `3.3V`, `i2c-5` (`0x44`, Pins 3/5) | \$2.50 | CRC-8 validated in `sensors_full.py` |
| ToF Sensor | VL53L1X Time-of-Flight Ranging Module | 1 | ST `VL53L1X` | `3.3V`, `i2c-5` (`0x29`, Pins 3/5) | \$3.50 | Desktop proximity gesture |
| Power | INA219 High-Side Power Telemetry Module | 1 | TI `INA219` | `3.3V`, `i2c-5` (`0x40`, Pins 3/5) | \$2.00 | Bus voltage/current logging |
| Feedback | 8-LED WS2812B Ring + 5V Buzzer | 1 set | Generic | `5V`, GPIO Pin 33 (via 2N7002 level shift) & Pin 31 | \$2.50 | Ambient status & haptic alert |
| Audio/Cam | USB Driver-Free Mic/Camera (or INMP441 + MAX98357A I2S) | 1 | Generic USB / I2S | `5V` USB 3.0 or `V_PRIVACY_3V3` I2S (Pins 12/35/38/40) | \$8.00 | Power-gated by DPDT in V1 |

### 1.3 V1 Custom Carrier PCB (`aura_x5_hat`) & 3D Enclosure (JLCPCB / LCSC Ready)

| Designator | Qty | Component | Package / Spec | LCSC SKU / MPN | Voltage / Role | Est. Cost (USD) |
|---|---|---|---|---|---|---|
| PCB | 1 | `aura_x5_hat` 2-Layer 85×56×1.6 mm 1 oz HASL | Gerber in `electronics/manufacturing/` | JLCPCB 2-Layer | 36 nets, 0 DRC errors | \$2.00 (5 pcs) |
| `U1` | 1 | AMS1117-3.3 3.3V 1A LDO Regulator | SOT-223-3 | LCSC `C6186` | `5V → 3.3V` dedicated peripheral rail | \$0.10 |
| `F1` | 1 | Resettable PTC Fuse | 0805 / Bourns `MF-R300` | LCSC `C70062` | `5V` input overcurrent protection | \$0.15 |
| `D1` | 1 | SMBJ5.0A TVS Surge/ESD Diode | SMB | LCSC `C173475` | `5V` transient clamp | \$0.12 |
| `Q1`, `Q2` | 2 | MMBT3904 / 2N3904 NPN Transistor | SOT-23-3 | LCSC `C20526` | Fan & Buzzer low-side PWM | \$0.06 |
| `Q3` | 1 | 2N7002 / 2N7000 N-MOSFET | SOT-23-3 | LCSC `C8545` | `3.3V → 5V` WS2812B level shift | \$0.05 |
| `D2`, `D3` | 2 | Red LED 0603 + 1N4148WS Flyback Diode | 0603 / SOD-323 | LCSC `C2286`, `C2128` | Privacy LED + fan flyback | \$0.08 |
| `R1..R8` | 7 | 1 kΩ (×4) & 10 kΩ (×3) 1% Resistors | 0603 | LCSC `C21190`, `C25804` | Pull-ups, RC debounce, base drive | \$0.10 |
| `C1..C6` | 6 | 10 µF 25V (×2) & 100 nF 50V (×4) Ceramic Caps | 0805 / 0603 | LCSC `C15850`, `C14663` | LDO bulk & GPIO debounce | \$0.12 |
| `J1..J11` | 1 set | 2×20P Female Stacking + 2×13P + Breakaway Pin Headers | 2.54 mm | Standard | 40-pin RDK stack & peripheral ports | \$1.50 |
| Enclosure | 3 pcs | `base_shell.stl` + `front_console_flat.stl` + `encoder_knob.stl` | PETG / Matte PLA+ (0.2 mm, 20%) | 3D Print (~98 cm³ total) | 15° ergonomic desktop housing | \$4.00 |

**Estimated Total Build Cost:** ~\$115 (V2 Solderless HDMI Core) / ~\$135 (Full V1 Custom HAT + All Optional Sensors + 3D Enclosure).

---

## 2. Schedule Through Final Demo (Nov 23 – Dec 15, 2026)

| Dates | Phase | Concrete Deliverables | Exit Gate |
|---|---|---|---|
| **Nov 23 – Nov 26** | Stage 1 & 2 Closure | Stage 1 screenshots, Stage 2 docs (`PROPOSAL`, `ARCHITECTURE`, `ENGINEERING_PLAN`, `ROADMAP`), public GitHub repo live, Discord updated, Stage 2 Showcase PR opened | Official Stage 2 PR open with all 6 required links |
| **Nov 27 – Dec 02** | ROS 2 Bring-Up on RDK X5 | `colcon build` of `aura_x5_ros`, live `ros2 launch`, `rqt_graph` & `ros2 topic hz` verification, physical GPIO wiring test (EC11 + Kill-Switch + DPDT) | All 4 ROS 2 nodes exchanging real messages on RDK X5 |
| **Dec 03 – Dec 07** | Continuous BPU + Concurrent Workload | Integrate continuous BPU inference (`hbm_runtime`) alongside 60 FPS HDMI UI + sensor hub; verify USB-C HID physical approval & Kill-Switch `<50 ms` abort | ≥60s continuous dual-workload soak test with zero errors |
| **Dec 08 – Dec 11** | Benchmarking & Physical Test Plan | Run `benchmark_bpu_concurrent.py`, complete all 8 tests in `physical_test_plan.csv`, record real FPS/latency/CPU/BPU/thermal numbers in `BENCHMARKS_AND_SAFETY.md` | Raw JSON & Markdown benchmark table committed |
| **Dec 12 – Dec 15** | Final Video, Docs & Advocacy | Shoot 3–7 min 1080p demo video (≥30s uncut continuous AI + physical approval + e-stop), publish 9+ external Advocator posts, update Showcase PR to **Stage 3** | Final Showcase PR merged/ready before Dec 15 23:59 |

---

## 3. Top Five Risks (Mitigation, Trigger & Fallback)

| # | Risk | Impact | Mitigation | Trigger Condition | Concrete Fallback |
|---|---|---|---|---|---|
| **1** | **Custom PCB (`aura_x5_hat`) fabrication/shipping or SMD soldering delay** | Blocks V1 physical HAT assembly before Dec 15 | Maintained dual-track hardware design from Day 1; 40-pin pinout is identical between V1 and V2 | PCB not delivered/assembled by **Dec 01** | Execute **V2 HDMI + Solderless DuPont Edition** (`docs/03_hdmi_solderless_guide.md`), which releases 100% of 40-pin GPIO for direct wiring while still publishing the DRC-clean V1 KiCad/Gerber pack |
| **2** | **USB-C OTG Gadget (`/dev/hidg0`) host OS enumeration or cable power drop** | Prevents hardware keyboard/mouse execution on Windows PC | Validate `libcomposite` descriptors on RDK X5 with a dedicated data-rated USB-C cable; power RDK X5 cleanly and log `/sys/class/udc` status | `/dev/hidg0` fails to enumerate on target Windows host after 2 debug attempts | Keep physical approval + Kill-Switch gating on RDK X5 over Ethernet/Wi-Fi WebSocket (`ws://192.168.128.10:8765`), forwarding signed physical decision events to the host companion executor while keeping `/dev/hidg0` documented & unit-tested |
| **3** | **BPU thermal throttling or CPU contention during concurrent workloads** | FPS jitter, frame drops, or SoC temperature exceeding 75 °C | Active 5V 30×30×7 mm fan driven by Pin 32 PWM; decouple UI rendering (60 FPS browser GPU/HDMI) from BPU thread via ROS 2 async callbacks; drop stale frames (`depth=2`) | `soc_temp_c >= 75 °C` or BPU FPS drops >25% over 60s soak test | Lock fan PWM to 100%, cap non-critical screen diff push to `2 Hz`, and use lightweight INT8 MobileNetV2 / YOLOv8n compiled `.bin` model |
| **4** | **High-DPI 4K desktop OCR accuracy degradation under 640×640 BPU input** | Unreadable small UI text (<14 px) leading to low-quality proactive suggestions | Pre-verified in our M2 resolution matrix: capture single primary display (`2560×1440`) and apply `640×640` tiling (`stride=512`) instead of downscaling full virtual desktop | OCR character accuracy `< 80%` on 14px+ desktop text | Combine foreground active-window metadata + focused active-window crop (`640×640` ROI around cursor/active app) for BPU visual classification/detection |
| **5** | **ROS 2 / TogetherROS Python environment mismatch on RDK X5** | `rclpy` cannot import `hbm_runtime` or `websockets` inside the same Python interpreter | Pin system Python 3.10 packages under `/opt/tros/humble` and keep core logic (`bpu_vision.py`, `agent_core.py`, `hal_devices.py`) in pure Python modules decoupled from `rclpy` | `ImportError` between `rclpy` and `hbm_runtime` during `colcon build` | Run `bpu_perception_node` with explicit `PYTHONPATH` pointing to `/usr/local/lib/python3.10/dist-packages` (system `hbm_runtime`), verified via `scripts/rdk_probe.py` |

---

## 4. Planned GitHub Repository Structure

Aligned with the official Stage 2 structure recommendation (`src/`, `launch/`, `models/`, `config/`, `docs/`, `tests/`):

```text
AURA-X5/
├── README.md                              # Setup, Quick Start, Stop/Recovery & Troubleshooting
├── LICENSE                                # MIT License
├── ROADMAP.md                             # Stage 1–3 public roadmap
├── interfaces.json                        # 40-Pin GPIO & protocol contract
├── ros2_ws/src/aura_x5_ros/               # ROS 2 package (src/, launch/, config/)
│   ├── aura_x5_ros/                       # ROS 2 nodes (sensor, BPU, safety gate, actuator/UI)
│   ├── launch/aura_x5.launch.py           # Unified launch file
│   └── config/aura_x5_params.yaml         # Pinned parameters & safety limits
├── firmware/                              # Hardware abstraction, BPU service, USB Gadget & UI servers
├── host/                                  # PC companion screen observer & proactive decision engine
├── ui_web/                                # Self-contained 60 FPS HDMI kiosk web UI
├── models/                                # Model manifest, download instructions & SHA/runtime metadata (no giant binaries committed)
├── electronics/                           # KiCad 9.0.7 schematics/PCB, DRC=0 report, BOM & Gerber zip
├── mechanical/                            # CadQuery STEP assembly, fit_check.json & watertight STLs
├── docs/                                  # STAGE1_IGNITE, PROPOSAL, ARCHITECTURE, ENGINEERING_PLAN, BENCHMARKS_AND_SAFETY, evidence/
├── scripts/                               # rdk_probe.py, deploy_to_rdk.py, benchmark_bpu_concurrent.py
├── verification/                          # Automated unit tests (test_aura_x5.py) & physical_test_plan.csv
└── showcase_pr/                           # Official challenge showcase Markdown draft
```
