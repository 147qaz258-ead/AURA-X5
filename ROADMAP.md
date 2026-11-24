# AURA-X5 Project Roadmap (Robotics Dream Keeper Challenge — 2026 Winter)

> **Final Submission Deadline:** December 15, 2026  
> **Judging:** December 16–31, 2026 · **Show & Tell / Awards:** January 7, 2027  
> This document serves as the public Stage 2 `ROADMAP.md` deliverable and mirrors our GitHub Project board.

---

## Milestone Overview

| Phase | Target Window | Milestone Goal | Status |
|---|---|---|---|
| **Pre-Work (M0–M2)** | Nov 13 – Nov 22, 2026 | Host observer validation (12 FPS 20-min 0% drop), 640-tile OCR probe, EVT-B KiCad PCB (DRC=0), CadQuery 3D enclosure, RDK X5 `hbm_runtime` BPU bring-up, V2 HDMI 60 FPS UI | **Completed** |
| **Stage 1 — Ignite** | Nov 23 – Nov 24, 2026 | Capture & organize Stage 1 bring-up evidence (RDK Studio + SSH, ES8326 I2S Mic + buses, YOLO11n BPU detection), publish personal GitHub repo & Showcase PR | **Completed (Nov 24)** |
| **Stage 2 — Build** | Nov 23 – Nov 26, 2026 | Finalize `PROPOSAL.md`, `ARCHITECTURE.md` (with ROS 2 node graph & compute plan), `ENGINEERING_PLAN.md` (BOM + Top-5 risks), update Discord & Showcase PR #15 | **Submitted (PR #15)** |
| **Stage 3A — Integration** | Nov 27 – Dec 05, 2026 | Deploy & verify `aura_x5_ros` ROS 2 nodes on RDK X5, integrate continuous BPU inference + concurrent UI/sensor pipeline, run USB-C HID physical approval + Kill-Switch HIL tests | **Planned** |
| **Stage 3B — Benchmarking** | Dec 06 – Dec 10, 2026 | Run ≥30s continuous dual-workload BPU benchmark (`benchmark_bpu_concurrent.py`), collect FPS/latency/CPU/BPU/thermal logs, execute all 8 steps of `physical_test_plan.csv` | **Planned** |
| **Stage 3C — Final Launch** | Dec 11 – Dec 15, 2026 | Record & edit 3–7 min 1080p demo video (≥30s uncut continuous AI operation + Kill-Switch demo), polish final docs, publish 9+ RDK Advocator external posts, submit final Stage 3 Showcase PR | **Planned (Hard Stop Dec 15)** |

---

## Detailed Task Board (GitHub Project Mirror)

### Backlog / Stage 1–2 Immediate Sprint (Nov 23 – Nov 26)
- [x] Verify RDK X5 SSH connectivity and `hbm_runtime 1.24.5` BPU execution (`scripts/test_bpu_on_rdk.py`)
- [x] Validate 40-pin GPIO zero-conflict hardware contract (`interfaces.json`)
- [x] Complete KiCad 9.0.7 PCB layout with 0 DRC errors and export Gerber/BOM (`electronics/`)
- [x] Generate watertight CadQuery 3D enclosure STLs (`mechanical/fit_check.json`)
- [x] Build V2 offline 60 FPS HDMI Web UI and solderless wiring guide (`ui_web/index.html`, `docs/03_hdmi_solderless_guide.md`)
- [x] Author Stage 2 core documents (`PROPOSAL.md`, `ARCHITECTURE.md`, `ENGINEERING_PLAN.md`, `ROADMAP.md`)
- [x] Scaffold ROS 2 package `aura_x5_ros` with launch file and parameter config (`ros2_ws/src/aura_x5_ros/`)
- [ ] Capture clean Stage 1 evidence images (RDK Studio flash + SSH terminal, peripheral photo/clip, AI screenshot) under `docs/evidence/stage1/`
- [ ] Push public personal repository (Warehouse A) and open Stage 2 Showcase PR to `D-Robotics/Robotics-Dream-Keeper-Challenge-Winter` (Warehouse B)
- [ ] Post Stage 1 & Stage 2 evidence links in personal Discord challenge thread

### Stage 3 Hardware & AI Integration Sprint (Nov 27 – Dec 10)
- [ ] `colcon build` and run `ros2 launch aura_x5_ros aura_x5.launch.py` on live RDK X5; capture `rqt_graph` and `ros2 topic hz` screenshots
- [ ] Wire physical EC11 encoder, Kill-Switch button, and DPDT privacy switch (V2 solderless or V1 HAT) and verify GPIO interrupts on RDK X5
- [ ] Upgrade continuous BPU perception workload (YOLOv8 / PP-OCRv5 / MobileNetV2 on `hbm_runtime`) running concurrently with 60 FPS HDMI UI + sensor telemetry
- [ ] Run `scripts/benchmark_bpu_concurrent.py --duration 60` on RDK X5 and commit raw JSON + Markdown benchmark table into `docs/BENCHMARKS_AND_SAFETY.md`
- [ ] Complete all 8 test cases in `verification/physical_test_plan.csv` (changing status from `NOT_RUN` to measured `PASS`/`FAIL` with logs)

### Stage 3 Packaging & Advocacy Sprint (Dec 11 – Dec 15)
- [ ] Record 1080p 3–7 min final demo video (hardware walkaround, ROS 2 live topics, ≥30s continuous BPU inference, physical approval executing real PC action, Kill-Switch immediate abort)
- [ ] Complete 9+ external community posts/videos per `docs/ADVOCATOR_CONTENT_PLAN.md` (with official D-Robotics referral links and verified metrics)
- [ ] Update Showcase PR to Stage 3 with final demo video URL, benchmark links, and final Discord thread permalink before **December 15, 2026**
