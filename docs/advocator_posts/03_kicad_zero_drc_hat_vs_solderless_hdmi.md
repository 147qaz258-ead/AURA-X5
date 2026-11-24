# 从 KiCad 0 DRC 报错到免焊 60 FPS HDMI：给 D-Robotics RDK X5 设计桌面具身 AI 终端的双路线硬件实战

> 本文为 **D-Robotics（地瓜机器人）Robotics Dream Keeper Challenge — 2026 Winter** 硬件工程分享（第 3 篇）。  
> - 官方赛事仓库：[D-Robotics/Robotics-Dream-Keeper-Challenge-Winter](https://github.com/D-Robotics/Robotics-Dream-Keeper-Challenge-Winter)  
> - D-Robotics 开发者文档：[https://developer.d-robotics.cc/en/documentation](https://developer.d-robotics.cc/en/documentation)  
> - 本项目完整 KiCad 工程 / Gerber / BOM / 3D STL 开源仓库：[https://github.com/147qaz258-ead/AURA-X5](https://github.com/147qaz258-ead/AURA-X5)

> **配图建议（发布时直接上传）：**  
> 1. 定制载板 3D 渲染图：`aura_x5/electronics/pcb_3d_top.png`  
> 2. 定制载板 2D 布线预览图：`aura_x5/electronics/pcb_preview.png`  
> 3. 15° 控制台 3D 外壳装配渲染图：`aura_x5/mechanical/cad_preview.png`

---

## 一、为什么同一个 RDK X5 项目要做“双路线硬件”？

在开源机器人硬件项目里，经常遇到一个两难问题：
- **做全定制 PCB + 3D 外壳**：整机颜值和集成度极高，但其他社区开发者想复刻时，要等打样、买贴片元件、自己焊接，门槛很高；
- **全用杜邦线搭积木**：上手快，但线束杂乱、缺少过流/防反接保护和规范的硬件隐私切断电路。

所以在为 **D-Robotics RDK X5** 设计桌面具身主动式 AI 终端 **AURA-X5** 时，我们坚持**“同一份 40-Pin 零冲突契约（`interfaces.json`）+ 同一套 ROS 2 固件，兼容两套硬件形态”**：
1. **V1 定制载板版（`aura_x5_hat`）**：完整 KiCad 9.0.7 原理图/PCB + Gerber 生产包 + CadQuery 3D 打印外壳，面向追求一体成型和硬件级安全电路的极客；
2. **V2 免焊 HDMI 60 FPS 版**：零焊接、40-Pin 全释放、母对母杜邦线直连，面向想在 1 小时内复刻上手的 RDK X5 开发者。

---

## 二、先定“单一真相源”：`interfaces.json` 锁死 40-Pin 零冲突

多外设叠加在 RDK X5 的 40-Pin 排针上，最容易出现 SPI、UART、I2C、I2S 与普通 GPIO 抢引脚的隐蔽 Bug。我们把整机全部接口写进单一契约文件 `interfaces.json`，并在单元测试 `verification/test_aura_x5.py` 中自动扫描每一组引脚，确保 **0 引脚冲突**：

| 子系统 | RDK X5 总线 / 接口 | 物理引脚（BOARD） | 接入外设 |
|---|---|---|---|
| **I2C 传感总线** | `i2c-5` | Pin 3 (SDA), Pin 5 (SCL) | VL53L1X (`0x29`), INA219 (`0x40`), SHT40 (`0x44`) |
| **SPI 屏与触控（V1）** | `spidev0/1` + GPIO | Pin 19/21/23/24/26/18/22/11 | 3.5" 480×320 ILI9486 + XPT2046 电阻触摸 |
| **毫米波存在雷达** | UART `/dev/ttyS1` (256000) | Pin 8 (TX), Pin 10 (RX) | HLK-LD2410C 24 GHz 人体存在雷达 |
| **音频接口（V1）** | I2S | Pin 12/35/38/40 | INMP441 麦克风（受 DPDT 硬断电）+ MAX98357A |
| **安全与人机控制** | `Hobot.GPIO` | Pin 7 (急停), Pin 13/15/16 (EC11), Pin 29 (隐私检测), Pin 31 (蜂鸣器), Pin 32 (风扇 PWM), Pin 33 (WS2812B) | 物理审批旋钮、Kill-Switch、硬件隐私开关、主动散热与光环 |

---

## 三、路线 V1：KiCad 9.0.7 定制载板（0 DRC 报错）+ CadQuery 参数化外壳

### 1. 定制扩展板 `aura_x5_hat`（EVT-B）关键电路
- **尺寸对齐**：`85.0 × 56.0 × 1.6 mm` 两层板，4 个 M2.5 安装孔与 RDK X5 严格同轴。
- **电源与保护**：输入端集成 3A 自恢复保险丝 `F1`（PTC）+ `SMBJ5.0A` TVS 瞬态抑制二极管 `D1`，板载独立 `AMS1117-3.3` 1A LDO 给外设单独供电，不拖垮 RDK X5 核心轨。
- **硬件隐私硬切断**：DPDT 拨动开关（`J3`）在电源物理层直接通断 `V_PRIVACY_3V3`，同步点亮/熄灭红色隐私指示灯 `D2`，并将电平回传至 `Pin 29`。
- **驱动与电平转换**：`MMBT3904` 低边 NPN 驱动 5V 风扇（带 `1N4148WS` 续流二极管）与蜂鸣器；`2N7002` N-MOSFET 实现 3.3V→5V 的 WS2812B 数据电平转换；EC11 与急停按键均配置硬件 RC 去抖（`10kΩ + 100nF`）。
- **自动化 DRC 验收结果**（`electronics/validation.json`）：
  - 元件数：**32** · 焊盘：**147** · 网络：**36** · 走线：**3,995** · 过孔：**69**
  - **KiCad DRC 错误数：`0`** · **未连接网络数：`0`**
  - 已完整导出标准 Gerber 生产压缩包与带立创商城编号（`C6186`、`C70062`、`C173475` 等）的 `bom_easyeda_native.csv`，上传嘉立创即可直接打样。

### 2. 参数化 3D 打印外壳（CadQuery 2.8.0）
利用代码参数化生成 15° 人体工学桌面控制台，包含 3 个打印件，全部通过 Mesh 封闭性检验（`mechanical/fit_check.json`）：
- `base_shell.stl`（`104 × 114 × 46 mm`，`72.77 cm³`，watertight = `true`）：底部进风 + 顶部后置排风风道；
- `front_console_flat.stl`（`104 × 90 × 4 mm`，`19.32 cm³`，watertight = `true`）：正面朝下免支撑打印；
- `encoder_knob.stl`（`Ø24 × 14 mm`，`5.99 cm³`，watertight = `true`）：EC11 实体审批旋钮帽。

---

## 四、路线 V2：HDMI 60 FPS + 免焊杜邦线直连方案

在调试过程中我们发现：如果把副屏切换为标准 **HDMI 小屏**，原本被 3.5" 屏占用的 26-Pin 接口瞬间 **100% 全部释放**！
1. **显示帧率直接起飞**：RDK X5 上直接运行轻量本地服务（HTTP `8080` + WebSocket `8765`），Chromium 以 `--kiosk --app=http://127.0.0.1:8080` 打开零外部 CDN 依赖的离线上位界面 `ui_web/index.html`，丝滑跑到 **60 FPS**。
2. **零焊接直连核心安全件**：只需 10 根母对母杜邦线即可直连 EC11 编码器（Pin 1/6/13/15/16）、Kill-Switch 急停（Pin 7/9）、DPDT 隐私开关（Pin 17/29）、HLK-LD2410C 雷达（Pin 2/8/10/14）和 5V 散热风扇（Pin 4/30）。
3. **音视频免焊即插即用**：USB 免驱麦/摄像头直接插 RDK X5 板载 USB 3.0 口，整机装配时间从“等打样 + 焊接半天”压缩到 **30 分钟**。

---

## 五、开源资料获取

无论你想直接拿去嘉立创打样 V1 定制载板，还是用杜邦线半小时搭出 V2 免焊版，所有源文件（KiCad / Gerber / 立创 BOM / STEP / STL / ROS 2 / 固件）均以 MIT 协议开源：

- **AURA-X5 项目仓库**：[https://github.com/147qaz258-ead/AURA-X5](https://github.com/147qaz258-ead/AURA-X5)
- **官方赛事仓库（RDK 冬季挑战赛）**：[https://github.com/D-Robotics/Robotics-Dream-Keeper-Challenge-Winter](https://github.com/D-Robotics/Robotics-Dream-Keeper-Challenge-Winter)
- **RDK Studio 下载**：[https://developer.d-robotics.cc/en/rdkstudio](https://developer.d-robotics.cc/en/rdkstudio)

下一篇我们将深入拆解 **RDK X5 USB-C OTG Composite Gadget（一根线模拟网卡 + 硬件键鼠）与 ROS 2 四节点实机联调**，敬请期待！
