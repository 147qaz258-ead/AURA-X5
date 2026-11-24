# AURA-X5 — RDK Advocator & TOP Voice ($500) External Content Plan

> **Official Rule (`awards.md`):** Publish **more than 8 qualifying items (≥ 9 posts/videos)** outside D-Robotics-owned communities during the 45-day competition window.  
> **Mandatory Per-Item Checklist:**
> 1. Clearly mention **D-Robotics**, **RDK**, or **RDK Challenge** (or **地瓜机器人 / RDK X5 / RDK 冬季挑战赛**).
> 2. Include **at least one official referral link**:
>    - Official Challenge Repo: `https://github.com/D-Robotics/Robotics-Dream-Keeper-Challenge-Winter`
>    - D-Robotics Developer Docs: `https://developer.d-robotics.cc/en/documentation`
>    - RDK Studio: `https://developer.d-robotics.cc/en/rdkstudio`
> 3. Keep every post public and archive the **permalink + verified view/read analytics screenshot**.

---

## Target Strategy
- **Guaranteed Baseline:** `RDK Advocator` title + official merchandise kit (mug, socks, mousepad, sticker) upon completing ≥ 9 compliant external posts.
- **Primary Competitive Target:** **TOP Voice — Writer ($500)** by turning our real engineering experiments (4K OCR tiling matrix, 0-DRC KiCad HAT, USB-C Composite HID + Kill-Switch, ROS 2 BPU architecture) into deeply citeable technical articles on Zhihu / CSDN / Juejin / Medium / Dev.to.
- **Secondary Competitive Target:** **TOP Voice — Producer ($500)** by publishing polished Bilibili + YouTube build/demo videos.

---

## 10-Post Engineering Content Matrix

| # | Target Date | Format & Platform | Working Title | Reusable Real Project Material | Official Mention & Link | Status | Public URL & Verified Views |
|---|---|---|---|---|---|---|---|
| 1 | Nov 24 | Tech Blog (Zhihu / CSDN) | 为什么纯软件桌面 Agent 不够？我用 D-Robotics RDK X5 造一台带物理隐私开关的具身第二大脑 | `docs/advocator_posts/01_aura_x5_embodied_desktop_agent.md` | RDK X5 + Challenge Repo | **Draft Ready** | `<url>` |
| 2 | Nov 24 | Deep-Dive Tech Blog (Zhihu / Juejin) | 4K 桌面做中文 OCR 为什么准确率跌到 12%？面向 D-Robotics RDK X5 640×640 BPU 输入的缩放与切片量化实测 | `docs/advocator_posts/02_4k_desktop_ocr_tiling_experiment_for_rdk_x5.md` | D-Robotics RDK X5 + Model Zoo | **Draft Ready** | `<url>` |
| 3 | Nov 24 | Hardware Blog + Pictures | 从 KiCad 0 DRC 报错到免焊 60 FPS HDMI：给 D-Robotics RDK X5 设计桌面具身 AI 终端的双路线硬件实战 | `docs/advocator_posts/03_kicad_zero_drc_hat_vs_solderless_hdmi.md` | D-Robotics RDK X5 + Docs | **Draft Ready** | `<url>` |
| 4 | Nov 26 | Tech Blog + Short Clip (Bilibili / X) | RDK X5 开箱、RDK Studio 烧录与 10 TOPS BPU (`hbm_runtime`) 首次实测踩坑记录 | `docs/STAGE1_IGNITE.md`, `scripts/test_bpu_on_rdk.py` | RDK Studio + Docs | Planned | `<url>` |
| 5 | Nov 29 | Deep-Dive Tech Blog | 20 分钟 12 FPS 零丢帧：面向边缘视觉协同的 Windows 实时屏幕变化检测工程实录 | `M1_acceptance.md` (`14,394` frames, `0.00%` drop, `26ms` stop) | RDK Challenge + Repo | Planned | `<url>` |
| 6 | Dec 03 | Maker Tutorial (Bilibili / Zhihu) | CadQuery 参数化 3D 打印外壳全解析：如何为 RDK X5 设计 15° 控制台散热风道与旋钮结构 | `mechanical/cad_preview.png`, `scripts/generate_mechanical.py` | RDK X5 + Challenge Repo | Planned | `<url>` |
| 7 | Dec 05 | Embedded Systems Blog | 一根 Type-C 线搞定网络+硬件键鼠：RDK X5 USB-C Composite Gadget 与 Kill-Switch 安全门控实战 | `firmware/usb_gadget_setup.sh`, `firmware/agent_core.py` | D-Robotics RDK X5 + Docs | Planned | `<url>` |
| 8 | Dec 07 | Robotics Architecture Blog | 在 RDK X5 上用 ROS 2 编排多传感器、BPU 视觉与 60 FPS 副屏 UI：从 WebSocket 到 `rqt_graph` | `docs/ARCHITECTURE.md`, `ros2_ws/src/aura_x5_ros/` | RDK X5 + Course Demos | Planned | `<url>` |
| 9 | Dec 10 | Benchmark Report | RDK X5 10 TOPS BPU 双并发负载实测：连续推理 FPS、延迟、温度曲线与散热调优 | `scripts/benchmark_bpu_concurrent.py`, `docs/BENCHMARKS_AND_SAFETY.md` | D-Robotics RDK X5 + Model Zoo | Planned | `<url>` |
| 10 | Dec 13 | Full Demo Video (Bilibili + YouTube) | 【RDK 冬季挑战赛】AURA-X5 完整开源演示：10 TOPS BPU 实时推理 + 物理旋钮审批 + 硬件急停 | Final 3–7 min 1080p demo video + GitHub release | RDK Challenge + Official Repo | Planned | `<url>` |
