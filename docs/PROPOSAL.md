# Stage 2 — Concept & Application Proposal: AURA-X5

> **Official Requirement:** [`stages/stage2-build.md` — Challenge 1](https://github.com/D-Robotics/Robotics-Dream-Keeper-Challenge-Winter/blob/main/stages/stage2-build.md)  
> **Project:** AURA-X5 · Desktop Embodied Proactive AI Co-Pilot  
> **Compute Baseline:** D-Robotics RDK X5 (10 TOPS BPU + 8-Core Cortex-A55)

---

## 1. Operating Scenario & Constraints

### Scenario
Knowledge workers, hardware/embedded engineers, and developers spend 6–10 hours a day at multi-monitor workstations switching between IDEs (VS Code, KiCad, PyCharm), terminals, browsers, and documentation. Existing AI assistants are either **purely reactive** (requiring manual copy-paste into chat boxes) or **intrusive software agents** that consume host GPU/CPU for continuous screen vision, interrupt flow with pop-up dialogs, and inject simulated clicks without any physical emergency stop or privacy guarantee.

**AURA-X5** sits directly beneath or beside the user's monitor as a **physical, embodied second brain** tethered to the PC over a single USB-C cable (plus optional LAN WebSocket):
- Continuously receives filtered desktop change frames and local desk-presence signals.
- Offloads visual perception to the **D-Robotics RDK X5 10-TOPS BPU**.
- Surfaces concise, evidence-backed proactive suggestions on a **dedicated external secondary screen** (15° ergonomic desktop console) without touching the user's primary workspace.
- Executes real keyboard/mouse macros on the host PC **only after explicit physical confirmation** (EC11 rotary press, touchscreen tap, or local kiosk confirm), and can be physically halted in milliseconds via a dedicated **Kill-Switch** or muted at the power-rail level via a **DPDT Privacy Switch**.

### Key Engineering Constraints
1. **Strict BPU Authenticity**: Edge visual inference must run on the RDK X5 Bayes BPU (`hbm_runtime`). Missing BPU runtime or model files must raise `BPUUnavailableError` (fail-fast) rather than silently falling back to CPU or cloud vision.
2. **Zero Unapproved Actuation**: No USB HID keystroke or mouse injection may execute without a verified physical approval event.
3. **Thermal & Footprint Envelope**: Desktop console dimensions limited to `104 × 114 × 46 mm` (`base_shell.stl`), requiring active 5V cooling airflow to keep RDK X5 BPU under `75 °C` during sustained concurrent workloads.
4. **High-DPI Desktop Readability Constraint (Empirically Verified)**: Prior controlled resolution experiments (see Section 5) proved that feeding a downscaled full virtual desktop (`5760×2160 → 1920×720`) directly into a `640×640` detector collapses Chinese text accuracy to `12%`. Therefore, perception must use **per-monitor capture + region/tile slicing (`640×640`)** rather than naive full-desktop squashing.

---

## 2. Intended Users & Interaction Model

### Target Users
- **Primary**: Software developers, robotics/embedded engineers, and technical researchers running Windows/Linux workstations who want proactive workflow assistance (auto-save reminders, build/log triage, focus-break locks, context capture) with strict local privacy.
- **Secondary**: RDK X5 community makers who want a reproducible, modular desktop embodied AI hardware kit (supporting both a **solderless HDMI + DuPont V2 build** and a **custom KiCad HAT + 3D-printed V1 build**).

### Embodied Human-in-the-Loop Interaction Loop
```text
[Desk Presence (mmWave Radar) + PC Screen Change (>2% diff)]
      │
      ▼
[RDK X5 BPU Continuous Visual Perception (hbm_runtime)]
      │
      ▼
[Proactive Suggestion + Evidence Frame ID + SHA-256 Hash]
      │
      ▼
[External Console Display (60 FPS HDMI UI / 3.5" SPI Touch) + WS2812B Status Ring]
      │
      ├── Rotate EC11 Encoder ──► Browse queued suggestions
      ├── Press EC11 / Tap APPROVE ──► Safety Gate verifies physical source ──► USB-C HID executes on PC
      ├── Tap REJECT ──► Dismiss & log rejection in JSONL audit trail
      ├── Press Kill-Switch (Pin 7) ──► Instant latch + abort queue + HID all-keys-release (<50 ms)
      └── Flip DPDT Privacy Switch ──► Physically severs V_PRIVACY_3V3 to Mic/Cam + Red LED
```

---

## 3. Core Perception, Decision & Actuation Capabilities

| Layer | Capability | Concrete Implementation |
|---|---|---|
| **Perception** | Desktop change detection & frame selection | Host PC `ScreenChangeDetector` (and validated 12 FPS `dsh-see-now` adapter) filters static frames and attaches `frame_id` + `SHA-256` |
| **Perception** | RDK X5 10-TOPS BPU inference | `bpu_perception_node` (`hbm_runtime` on Bayes BPU) runs continuous real-time visual classification/detection on incoming frames and/or local camera feed |
| **Perception** | Multi-sensor desk context | `sensor_node` polls HLK-LD2410C 24 GHz mmWave radar (user presence & distance), SHT40 (temp/RH), VL53L1X (proximity), INA219 (power), and GPIO privacy/button states |
| **Decision** | Context-aware proactive engine | Evaluates active window, screen diff ratio, BPU semantics, and focus duration (deterministic rules + optional LLM enrichment via env-injected API key) |
| **Decision** | Safety-gated approval state machine | `safety_gate_node` (`SafetyGatedAgentCore`) strictly rejects non-physical approvals and enforces Kill-Switch latching |
| **Actuation** | Hardware USB-C HID keyboard/mouse | Linux `libcomposite` USB Gadget (`/dev/hidg0`, `/dev/hidg1`) executes OS-native macros (`Ctrl+S`, `Win+L`, custom actions) immune to software UAC hooks |
| **Actuation** | Physical & visual feedback | 60 FPS HDMI Web UI (`ui_web/index.html`) or 3.5" SPI display, WS2812B RGB status ring, 5V PWM cooling fan thermal control, and 5V haptic buzzer |

---

## 4. Innovation Compared with Stock Demos

1. **Embodied Hardware Safety & Privacy Sovereignty**: Unlike stock vision demos that simply draw bounding boxes on a screen, AURA-X5 introduces a **DPDT hardware power-cut privacy rail** (`V_PRIVACY_3V3`), a **non-bypassable physical approval gate**, and a **hardware Kill-Switch** that guarantees zero stuck HID keys.
2. **Single-Cable USB-C Composite Gadget Architecture**: Turns the RDK X5 USB 2.0 Type-C OTG port into a simultaneous **CDC ECM/RNDIS network interface + Boot Keyboard HID + Boot Mouse HID**, enabling true PC-tethered robotics without host driver hacking.
3. **ROS 2 Modular Edge-Host Orchestration**: Bridges desktop host intelligence with standard ROS 2 topics/services on RDK X5, making every sensor, BPU inference stream, and safety state inspectable via `ros2 topic` and `rqt_graph`.
4. **Dual-Track Open Hardware Accessibility (V1 Custom HAT + V2 Solderless HDMI)**: Provides complete, DRC-clean KiCad 9.0.7 PCB manufacturing packages + watertight CadQuery 3D-print files **and** a zero-solder HDMI + DuPont path so any RDK X5 developer can replicate the system in under an hour.
5. **Empirical Pre-Validation Before Fabrication**: Grounded in real pre-build engineering benchmarks — 20-minute continuous 12 FPS capture (0.00% frame drop) and 90-line controlled OCR scale/tiling matrix experiments proving why `640×640` tiling is mandatory for X5 BPU text perception.

---

## 5. Measurable Success Targets

> Note: Targets below are explicit **Stage 3 engineering acceptance goals**. Already-verified pre-work baselines are clearly tagged `[VERIFIED]`; Stage 3 hardware targets are tagged `[TARGET — TO BE MEASURED ON RDK X5]`.

| Metric | Target Value | Verification Method | Current Status |
|---|---|---|---|
| Host screen capture stability | 12 FPS for ≥20 min, frame drop `< 2%` | Automated 20-min capture log | `[VERIFIED]` 12.00 FPS, 0.00% drop (14,394 frames) |
| 40-pin GPIO contract conflicts | `0` pin conflicts | Automated unit test `test_aura_x5.py` | `[VERIFIED]` 0 conflicts |
| Custom HAT PCB DRC errors | `0` DRC errors, `0` unconnected nets | KiCad 9.0.7 DRC (`validation.json`) | `[VERIFIED]` 0 errors, 0 unconnected |
| 3D enclosure printability | 100% watertight meshes (3/3 STL parts) | CadQuery/trimesh check (`fit_check.json`) | `[VERIFIED]` 3/3 watertight |
| Continuous BPU inference throughput | `≥ 20 FPS` (MobileNetV2) or `≥ 10 FPS` (YOLOv8s) continuously for `≥ 30 s` | `scripts/benchmark_bpu_concurrent.py` on RDK X5 | `[TARGET]` Stage 3 benchmark |
| Concurrent dual-workload stability | BPU inference + concurrent UI/sensor ROS 2 loop with `0` crashes over `≥ 60 s` | ROS 2 multi-node soak test + `ros2 topic hz` | `[TARGET]` Stage 3 benchmark |
| Unapproved HID execution count | `0` unauthorized injections | Safety gate unit + HIL test (`remote_api` rejected) | `[VERIFIED IN UNIT]` / `[TARGET IN HIL]` |
| Kill-Switch abort latency | `< 50 ms` from button press to HID all-zero release | Physical HIL test (`physical_test_plan.csv` Step 7) | `[TARGET]` Stage 3 HIL |
| Sustained BPU thermal ceiling | SoC / BPU temperature `< 75 °C` with active 5V fan | Thermal log during concurrent BPU soak test | `[TARGET]` Stage 3 benchmark |
