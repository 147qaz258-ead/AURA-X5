# AURA-X5 V2 · HDMI 大屏 + 免焊直连硬件方案

当切换为 **无触摸 HDMI 显示屏** 时，RDK X5 的 **40-Pin 排针将 100% 释放**，无需焊接定制扩展板，直接使用母对母杜邦线即可完成全套外设直连。

## 1. 免焊 40-Pin 杜邦线直连对照表

| 外设模块 | 模块引脚 | RDK X5 物理引脚（BOARD） | 说明 |
| :--- | :--- | :--- | :--- |
| **EC11 旋转编码器** | GND / + / SW / DT / CLK | Pin 6 / Pin 1(3.3V) / Pin 16 / Pin 15 / Pin 13 | 旋转切建议，按下批准 |
| **急停按键 (Kill-Switch)** | 一端 / 另一端 | Pin 9(GND) / Pin 7 | 常开按钮，按下急停 |
| **硬件隐私开关 (DPDT)** | 公共端 / 检测端 | Pin 17(3.3V) / Pin 29 (串 10k 下拉) | 同步硬切断麦克风供电 |
| **HLK-LD2410C 毫米波雷达** | 5V / GND / TX / RX | Pin 2(5V) / Pin 14(GND) / Pin 10(RX) / Pin 8(TX) | 注意 TX↔RX 交叉接 |
| **I2C 传感 (SHT40/VL53L1X)** | VCC / GND / SDA / SCL | Pin 1(3.3V) / Pin 20(GND) / Pin 3 / Pin 5 | 按需选配 |
| **5V 散热风扇** | 正极 / 负极 | Pin 4(5V) / Pin 30(GND) | 常转直连（或加三极管接 Pin 32 PWM） |
| **音频 & 视觉（免杜邦线）** | USB 免驱麦/音箱/摄像头 | RDK X5 板载 USB 3.0 口 | 即插即用，零焊接 |

## 2. HDMI 60 FPS 动态 UI 启动方式

```bash
# 在 RDK X5 上启动 V2 服务端（HTTP 8080 + WebSocket 8765）
python3 /opt/aura_x5/hdmi_server.py &

# 在 HDMI 桌面全屏无边框打开 60 FPS 界面
chromium-browser --kiosk --app=http://127.0.0.1:8080
```
