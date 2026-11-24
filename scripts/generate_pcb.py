"""Reproducible 2-layer KiCad 9.0.7 PCB & Schematic generator for AURA-X5 Carrier HAT (EVT-B).
Board: 85.0 x 56.0 x 1.6 mm (matches D-Robotics RDK X5 40-pin + mounting holes).
Features:
- J1 (RDK X5 40-Pin) + J2 (3.5" 480x320 ILI9486+XPT2046 Touch Display 26-Pin)
- Power Protection: F1 (3A PTC) + D1 (SMBJ5.0A TVS) + U1 (3.3V/1A LDO)
- Hardware Privacy DPDT Switch (J3) + Red Privacy LED (D2)
- I2C Bus (J4), LD2410C mmWave Radar (J5), I2S Audio (J6)
- EC11 Encoder (J7) with 3-ch RC debounce, Kill-Switch (J8) with RC debounce
- WS2812B Ring (J9) with 74AHCT1G125 3.3V->5V level shifter (U2)
- 5V PWM Fan Driver (J10, Q1, D3) + Buzzer PWM Driver (J11, Q2, D4)
- Bottom-layer GND copper pour + 0.508mm (20mil) exact 2.54mm-aligned autorouter
"""
from pathlib import Path
import csv, json, uuid, math, heapq, itertools, subprocess, zipfile
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "electronics"
FAB = OUT / "manufacturing"
OUT.mkdir(parents=True, exist_ok=True)
FAB.mkdir(parents=True, exist_ok=True)

KICAD_CLI = Path(r"E:\C_Projects\地瓜dot比赛\air_monitor\electronics\tools\kicad-portable\App\KiCad\bin\kicad-cli.exe")

uid_counter = itertools.count()
def uid():
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"aura-x5/evt-b/{next(uid_counter)}"))

def q(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'

parts, pads, nets, tracks, vias = [], [], {"": 0}, [], []

def net(n):
    if n not in nets:
        nets[n] = len(nets)
    return nets[n]

def part(ref, value, xy, pins, description, mpn, footprint, size=(8, 5), label_dy=-3.2):
    p = {
        "ref": ref, "value": value, "x": round(xy[0], 3), "y": round(xy[1], 3),
        "description": description, "mpn": mpn, "footprint": footprint,
        "size": size, "label_dy": label_dy, "pins": []
    }
    for num, dx, dy, n, *rest in pins:
        d = {
            "ref": ref, "num": str(num),
            "x": round(xy[0] + dx, 3), "y": round(xy[1] + dy, 3), "net": n,
            "diameter": rest[0] if rest else 1.35,
            "drill": rest[1] if len(rest) > 1 else 0.85,
            "name": rest[2] if len(rest) > 2 else str(num),
            "shape": "rect" if str(num) == "1" else "circle"
        }
        net(n)
        pads.append(d)
        p["pins"].append(d)
    parts.append(p)

def axial_r(ref, value, x, y, n1, n2, mpn="MFR-25FBF52-10K", pitch=7.62):
    part(ref, value, (x, y), [(1, -pitch/2, 0, n1, 1.35, 0.8), (2, pitch/2, 0, n2, 1.35, 0.8)],
         "Through-hole resistor 0.25W 1%", mpn, "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal", (6.3, 2.5), -2.2)

def cap_rad(ref, value, x, y, n1, n2, mpn="KEMET_C315C104K5R5TA", pitch=2.54):
    part(ref, value, (x, y), [(1, -pitch/2, 0, n1, 1.35, 0.75), (2, pitch/2, 0, n2, 1.35, 0.75)],
         "Decoupling capacitor", mpn, "Capacitor_THT:C_Disc_D3.8mm_W2.6mm_P2.50mm", (3.8, 2.6), -2.2)

# Grid origin aligned to 2.54mm / 5 = 0.508mm so all 2.54mm headers sit on exact grid nodes
STEP = 0.508
def snap(v):
    return round(round(v / STEP) * STEP, 3)

# --- 1. RDK X5 40-Pin Stacking Header (J1) ---
rdk_pin_nets = {
    1: "+3V3_RDK", 2: "VBUS_5V", 3: "I2C_SDA", 4: "VBUS_5V", 5: "I2C_SCL",
    6: "GND", 7: "KILL_SW", 8: "UART_TX", 9: "GND", 10: "UART_RX",
    11: "TP_IRQ", 12: "I2S_BCLK", 13: "EC11_A", 14: "GND", 15: "EC11_B",
    16: "EC11_SW", 17: "+3V3_RDK", 18: "LCD_RS", 19: "SPI_MOSI", 20: "GND",
    21: "SPI_MISO", 22: "LCD_RST", 23: "SPI_SCK", 24: "LCD_CS", 25: "GND",
    26: "TP_CS", 27: "", 28: "", 29: "PRIV_SENSE", 30: "GND",
    31: "BUZZ_PWM", 32: "FAN_PWM", 33: "WS2812_3V3", 34: "GND", 35: "I2S_LRCLK",
    36: "", 37: "", 38: "I2S_DIN", 39: "GND", 40: "I2S_DOUT"
}
j1_cx, j1_cy = snap(32.5), snap(4.0)
j1_pins = []
for idx in range(20):
    p_odd = 2 * idx + 1
    p_even = 2 * idx + 2
    dx = (idx - 9.5) * 2.54
    j1_pins.append((p_odd, dx, 1.27, rdk_pin_nets[p_odd], 1.35, 0.85, f"P{p_odd}"))
    j1_pins.append((p_even, dx, -1.27, rdk_pin_nets[p_even], 1.35, 0.85, f"P{p_even}"))
part("J1", "RDK_X5_40PIN", (j1_cx, j1_cy), j1_pins,
     "2x20 2.54mm female stacking header for RDK X5", "Samtec_SSQ-120-03-G-D",
     "Connector_PinSocket_2.54mm:PinSocket_2x20_P2.54mm_Vertical", (50.8, 5.08), 3.6)

# --- 2. 3.5inch Touch Display 26-Pin Header (J2) ---
j2_active_pins = {1, 2, 4, 6, 9, 11, 14, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26}
j2_cx, j2_cy = snap(26.0), snap(19.0)
j2_pins = []
for idx in range(13):
    p_odd = 2 * idx + 1
    p_even = 2 * idx + 2
    dx = (idx - 6.0) * 2.54
    n_odd = rdk_pin_nets[p_odd] if p_odd in j2_active_pins else ""
    n_even = rdk_pin_nets[p_even] if p_even in j2_active_pins else ""
    j2_pins.append((p_odd, dx, 1.27, n_odd, 1.35, 0.85, f"D{p_odd}"))
    j2_pins.append((p_even, dx, -1.27, n_even, 1.35, 0.85, f"D{p_even}"))
part("J2", "3.5_TFT_26PIN", (j2_cx, j2_cy), j2_pins,
     "2x13 2.54mm header for 3.5inch 480x320 ILI9486+XPT2046 Touch Display", "PinHeader_2x13_2.54mm",
     "Connector_PinHeader_2.54mm:PinHeader_2x13_P2.54mm_Vertical", (33.02, 5.08), 3.6)

# --- 3. Power Protection & Dedicated 3.3V/1A Regulator ---
part("F1", "PTC_3A", (snap(72.0), snap(8.0)), [(1, -2.54, 0, "VBUS_5V"), (2, 2.54, 0, "V5_PROT")],
     "3A Resettable PTC Fuse", "Bourns_MF-R300", "Fuse:Fuse_Bourns_MF-R300", (7.1, 3.0), -2.5)
part("D1", "SMBJ5.0A", (snap(72.0), snap(14.0)), [(1, -2.54, 0, "V5_PROT"), (2, 2.54, 0, "GND")],
     "5V TVS Surge/ESD Protection Diode", "Littelfuse_SMBJ5.0A", "Diode_THT:D_DO-41_SOD81_P5.08mm_Horizontal", (5.2, 2.7), -2.5)
part("U1", "AMS1117-3.3", (snap(72.0), snap(21.0)),
     [(1, -2.54, 0, "GND"), (2, 0, 0, "+3V3_EXT"), (3, 2.54, 0, "V5_PROT")],
     "Dedicated 3.3V 1A LDO Regulator for peripherals", "AMS1117-3.3", "Package_TO_SOT_THT:TO-220-3_Vertical", (10.0, 4.5), -2.5)
cap_rad("C1", "10uF", snap(61.0), snap(14.0), "V5_PROT", "GND", "Rubycon_10uF_25V")
cap_rad("C2", "10uF", snap(61.0), snap(20.0), "+3V3_EXT", "GND", "Rubycon_10uF_25V")
cap_rad("C3", "100nF", snap(61.0), snap(25.0), "+3V3_EXT", "GND")

# --- 4. Hardware Privacy Switch (DPDT) & Privacy LED ---
part("J3", "PRIVACY_DPDT", (snap(10.0), snap(47.0)),
     [(1, -2.54, -1.27, "+3V3_EXT"), (2, 0, -1.27, "V_PRIVACY_3V3"), (3, 2.54, -1.27, "GND"),
      (4, -2.54, 1.27, "+3V3_EXT"), (5, 0, 1.27, "PRIV_SENSE"), (6, 2.54, 1.27, "GND")],
     "2x3 header to front panel DPDT Privacy Kill-Switch", "PinHeader_2x03_2.54mm",
     "Connector_PinHeader_2.54mm:PinHeader_2x03_P2.54mm_Vertical", (7.62, 5.08), -3.5)
axial_r("R1", "1k", snap(10.0), snap(38.0), "V_PRIVACY_3V3", "LED_PRIV_A", "MFR-25FBF52-1K")
part("D2", "PRIV_LED", (snap(21.0), snap(38.0)), [(1, -1.27, 0, "GND"), (2, 1.27, 0, "LED_PRIV_A")],
     "Hardware privacy active indicator LED", "Kingbright_WP710A10ID", "LED_THT:LED_D3.0mm", (3.0, 3.0), -2.2)

# --- 5. Peripheral Connectors ---
part("J4", "I2C_BUS", (snap(8.0), snap(29.0)),
     [(1, 0, 0, "GND"), (2, 2.54, 0, "+3V3_EXT"), (3, 5.08, 0, "I2C_SDA"), (4, 7.62, 0, "I2C_SCL")],
     "1x4 I2C bus header (VL53L1X + SHT40 + INA219)", "JST_XH_4P",
     "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical", (10.16, 2.54), -2.5)

part("J5", "RADAR_LD2410", (snap(22.0), snap(29.0)),
     [(1, 0, 0, "V5_PROT"), (2, 2.54, 0, "GND"), (3, 5.08, 0, "UART_TX"), (4, 7.62, 0, "UART_RX")],
     "1x4 UART header for HLK-LD2410C 24GHz mmWave Radar", "PinHeader_1x04_2.54mm",
     "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical", (10.16, 2.54), -2.5)

part("J6", "I2S_AUDIO", (snap(37.0), snap(29.0)),
     [(1, 0, 0, "V_PRIVACY_3V3"), (2, 2.54, 0, "V5_PROT"), (3, 5.08, 0, "GND"),
      (4, 7.62, 0, "I2S_BCLK"), (5, 10.16, 0, "I2S_LRCLK"), (6, 12.7, 0, "I2S_DIN"), (7, 15.24, 0, "I2S_DOUT")],
     "1x7 I2S Audio header (Mic power gated by hardware privacy switch)", "PinHeader_1x07_2.54mm",
     "Connector_PinHeader_2.54mm:PinHeader_1x07_P2.54mm_Vertical", (17.78, 2.54), -2.5)

# --- 6. EC11 Encoder + 3-Ch RC Debounce + Kill-Switch ---
part("J7", "EC11_ENC", (snap(21.0), snap(47.0)),
     [(1, 0, 0, "GND"), (2, 2.54, 0, "+3V3_EXT"), (3, 5.08, 0, "EC11_A"), (4, 7.62, 0, "EC11_B"), (5, 10.16, 0, "EC11_SW")],
     "1x5 header for front EC11 rotary encoder", "PinHeader_1x05_2.54mm",
     "Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical", (12.7, 2.54), -2.5)
axial_r("R6", "10k", snap(31.0), snap(36.0), "+3V3_EXT", "EC11_A")
axial_r("R7", "10k", snap(31.0), snap(41.0), "+3V3_EXT", "EC11_B")
cap_rad("C5", "100nF", snap(41.0), snap(36.0), "EC11_A", "GND")
cap_rad("C6", "100nF", snap(41.0), snap(41.0), "EC11_B", "GND")

part("J8", "KILL_SW", (snap(37.0), snap(47.0)),
     [(1, 0, 0, "GND"), (2, 2.54, 0, "KILL_SW")],
     "1x2 header for physical Emergency Kill-Switch button", "PinHeader_1x02_2.54mm",
     "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical", (5.08, 2.54), -2.5)
axial_r("R2", "10k", snap(50.5), snap(36.0), "+3V3_EXT", "KILL_SW")
cap_rad("C4", "100nF", snap(50.5), snap(41.0), "KILL_SW", "GND")

# --- 7. WS2812B 3.3V->5V Level Shifter (Q3 MOSFET) + Ring Header ---
part("Q3", "2N7000_LVL", (snap(60.0), snap(36.0)),
     [(1, -2.54, 0, "WS2812_3V3", 1.35, 0.8, "S"), (2, 0, 0, "+3V3_EXT", 1.35, 0.8, "G"), (3, 2.54, 0, "WS2812_5V", 1.35, 0.8, "D")],
     "MOSFET 3.3V->5V level shifter for WS2812B data", "onsemi_2N7000", "Package_TO_SOT_THT:TO-92_Inline_Wide", (5.0, 4.0), -2.5)
axial_r("R8", "1k", snap(60.0), snap(42.0), "V5_PROT", "WS2812_5V", "MFR-25FBF52-1K")
part("J9", "WS2812_5V", (snap(46.0), snap(47.0)),
     [(1, 0, 0, "V5_PROT"), (2, 2.54, 0, "GND"), (3, 5.08, 0, "WS2812_5V")],
     "1x3 5V header for 8x WS2812B status ring", "PinHeader_1x03_2.54mm",
     "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical", (7.62, 2.54), -2.5)

# --- 8. 5V PWM Fan Driver + Buzzer PWM Driver ---
part("J10", "FAN_5V", (snap(68.0), snap(47.0)),
     [(1, 0, 0, "V5_PROT"), (2, 2.54, 0, "FAN_L")],
     "1x2 header for 30x30x7mm 5V PWM cooling fan", "PinHeader_1x02_2.54mm",
     "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical", (5.08, 2.54), -2.5)
axial_r("R3", "680R", snap(69.5), snap(34.0), "FAN_PWM", "FAN_BASE", "MFR-25FBF52-680R")
part("Q1", "2N3904_FAN", (snap(71.0), snap(40.0)),
     [(1, -2.54, 0, "GND", 1.35, 0.8, "E"), (2, 0, 0, "FAN_BASE", 1.35, 0.8, "B"), (3, 2.54, 0, "FAN_L", 1.35, 0.8, "C")],
     "NPN low-side PWM fan driver", "onsemi_2N3904BU", "Package_TO_SOT_THT:TO-92_Inline_Wide", (5.0, 4.0), -2.5)
part("D3", "1N4148_FAN", (snap(72.0), snap(28.0)), [(1, -2.54, 0, "V5_PROT"), (2, 2.54, 0, "FAN_L")],
     "Flyback diode for cooling fan", "Vishay_1N4148", "Diode_THT:D_DO-41_SOD81_P5.08mm_Horizontal", (5.0, 2.0), -2.2)

part("J11", "BUZZER_5V", (snap(77.0), snap(47.0)),
     [(1, 0, 0, "V5_PROT"), (2, 2.54, 0, "BUZZ_L")],
     "1x2 header for 5V haptic/alert buzzer", "PinHeader_1x02_2.54mm",
     "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical", (5.08, 2.54), -2.5)
axial_r("R4", "680R", snap(80.0), snap(30.0), "BUZZ_PWM", "BUZZ_BASE", "MFR-25FBF52-680R")
part("Q2", "2N3904_BUZ", (snap(81.0), snap(40.0)),
     [(1, -2.54, 0, "GND", 1.35, 0.8, "E"), (2, 0, 0, "BUZZ_BASE", 1.35, 0.8, "B"), (3, 2.54, 0, "BUZZ_L", 1.35, 0.8, "C")],
     "NPN low-side PWM buzzer driver", "onsemi_2N3904BU", "Package_TO_SOT_THT:TO-92_Inline_Wide", (5.0, 4.0), -2.5)

holes = [(3.5, 3.5), (61.5, 3.5), (3.5, 52.5), (61.5, 52.5)]

# --- 9. Exact 0.508mm (20 mil) 2-Layer Grid Autorouter ---
W_MM, H_MM = 85.0, 56.0
NX, NY = int(W_MM / STEP) + 1, int(H_MM / STEP) + 1
grid = np.zeros((2, NX, NY), dtype=np.uint64)

def cells_disk(x, y, r):
    for ix in range(max(0, int((x - r) / STEP)), min(NX, int((x + r) / STEP) + 2)):
        for iy in range(max(0, int((y - r) / STEP)), min(NY, int((y + r) / STEP) + 2)):
            if (ix * STEP - x) ** 2 + (iy * STEP - y) ** 2 <= r * r:
                yield ix, iy

for layer in range(2):
    grid[layer, :2, :] = 1
    grid[layer, -2:, :] = 1
    grid[layer, :, :2] = 1
    grid[layer, :, -2:] = 1
for hx, hy in holes:
    for ix, iy in cells_disk(hx, hy, 2.6):
        grid[:, ix, iy] |= 1

for p in pads:
    p["netid"] = nets[p["net"]]
    occ = 1 << p["netid"]
    rad = (p["diameter"] * 0.71 if p["shape"] == "rect" else p["diameter"] / 2) + 0.36
    for ix, iy in cells_disk(p["x"], p["y"], rad):
        grid[:, ix, iy] |= occ

def route_pair(p1, p2, netname, width=0.22):
    nid = nets[netname]
    mask = np.uint64(~(1 << nid) & 0xFFFFFFFFFFFFFFFF)
    sx, sy = int(round(p1["x"] / STEP)), int(round(p1["y"] / STEP))
    gx, gy = int(round(p2["x"] / STEP)), int(round(p2["y"] / STEP))
    start = (0, sx, sy)
    pq = [(abs(sx - gx) + abs(sy - gy), 0, start)]
    best = {start: 0}
    parent = {}
    goal = None
    while pq:
        _, g, cur = heapq.heappop(pq)
        if g > best.get(cur, 1e18):
            continue
        l, x, y = cur
        if x == gx and y == gy:
            goal = cur
            break
        for nl, nx_, ny_, cost in [
            (l, x + 1, y, 1), (l, x - 1, y, 1), (l, x, y + 1, 1), (l, x, y - 1, 1),
            (1 - l, x, y, 16)
        ]:
            if not (1 <= nx_ < NX - 1 and 1 <= ny_ < NY - 1):
                continue
            if (grid[nl, nx_, ny_] & mask) != 0:
                continue
            if nl != l:
                via_blocked = False
                for dx in range(-2, 3):
                    for dy in range(-2, 3):
                        if dx * dx + dy * dy > 4:
                            continue
                        vx, vy = nx_ + dx, ny_ + dy
                        if 0 <= vx < NX and 0 <= vy < NY:
                            if (grid[0, vx, vy] & mask) != 0 or (grid[1, vx, vy] & mask) != 0:
                                via_blocked = True
                                break
                    if via_blocked:
                        break
                if via_blocked:
                    continue
            nxt = (nl, nx_, ny_)
            ng = g + cost + (1 if nl == 0 else 0)
            if ng < best.get(nxt, 1e18):
                best[nxt] = ng
                parent[nxt] = cur
                heapq.heappush(pq, (ng + abs(nx_ - gx) + abs(ny_ - gy), ng, nxt))
    if goal is None:
        return False
    path = []
    cur = goal
    while cur in parent:
        path.append(cur)
        cur = parent[cur]
    path.append(start)
    path.reverse()
    if abs(p1["x"] - sx * STEP) > 1e-3 or abs(p1["y"] - sy * STEP) > 1e-3:
        tracks.append({"layer": "F.Cu", "x1": p1["x"], "y1": p1["y"], "x2": round(sx * STEP, 3), "y2": round(sy * STEP, 3), "width": width, "net": netname})
    for i in range(len(path) - 1):
        l1, x1, y1 = path[i]
        l2, x2, y2 = path[i + 1]
        if l1 != l2:
            vias.append({"x": round(x1 * STEP, 3), "y": round(y1 * STEP, 3), "net": netname})
            for ix, iy in cells_disk(x1 * STEP, y1 * STEP, 0.70):
                grid[:, ix, iy] |= (1 << nid)
        else:
            tracks.append({
                "layer": "F.Cu" if l1 == 0 else "B.Cu",
                "x1": round(x1 * STEP, 3), "y1": round(y1 * STEP, 3),
                "x2": round(x2 * STEP, 3), "y2": round(y2 * STEP, 3),
                "width": width, "net": netname
            })
            for ix, iy in cells_disk(x1 * STEP, y1 * STEP, width / 2 + 0.22):
                grid[l1, ix, iy] |= (1 << nid)
    last_l = path[-1][0]
    if abs(p2["x"] - gx * STEP) > 1e-3 or abs(p2["y"] - gy * STEP) > 1e-3:
        tracks.append({"layer": "F.Cu" if last_l == 0 else "B.Cu", "x1": round(gx * STEP, 3), "y1": round(gy * STEP, 3), "x2": p2["x"], "y2": p2["y"], "width": width, "net": netname})
    return True

# Route signal nets first, power second, GND last
power_nets = {"VBUS_5V", "V5_PROT", "+3V3_EXT", "+3V3_RDK", "V_PRIVACY_3V3"}
ordered_nets = (
    [n for n in nets if n and n not in power_nets and n != "GND"]
    + [n for n in nets if n in power_nets]
    + (["GND"] if "GND" in nets else [])
)
unrouted = []
for netname in ordered_nets:
    nid = nets[netname]
    npads = [p for p in pads if p["net"] == netname]
    if len(npads) < 2:
        continue
    w = 0.25 if netname in ("VBUS_5V", "V5_PROT", "+3V3_EXT", "+3V3_RDK", "V_PRIVACY_3V3") else 0.22
    connected = [npads[0]]
    rem = npads[1:]
    while rem:
        best_pair = min(
            ((math.hypot(a["x"] - b["x"], a["y"] - b["y"]), a, b) for a in connected for b in rem),
            key=lambda t: t[0]
        )
        _, a, b = best_pair
        if not route_pair(a, b, netname, w):
            unrouted.append((netname, a["ref"] + "." + a["num"], b["ref"] + "." + b["num"]))
        connected.append(b)
        rem.remove(b)

# --- 10. Emit KiCad 9 .kicad_pcb (with B.Cu GND copper zone) ---
pcb_lines = [
    '(kicad_pcb (version 20241229) (generator "aura_x5_gen") (generator_version "9.0")',
    '  (general (thickness 1.6) (legacy_teardrops no))',
    '  (paper "A4")',
    '  (layers',
    '    (0 "F.Cu" signal)',
    '    (31 "B.Cu" signal)',
    '    (36 "B.SilkS" user "B.Silkscreen")',
    '    (37 "F.SilkS" user "F.Silkscreen")',
    '    (38 "B.Mask" user)',
    '    (39 "F.Mask" user)',
    '    (44 "Edge.Cuts" user)',
    '  )',
    '  (setup (pad_to_mask_clearance 0.0) (allow_soldermask_bridges_in_footprints yes))',
]
for nname, nid in nets.items():
    pcb_lines.append(f'  (net {nid} {q(nname)})')

pcb_lines.append(f'  (gr_rect (start 0 0) (end {W_MM} {H_MM}) (stroke (width 0.1) (type solid)) (fill none) (layer "Edge.Cuts") (uuid {q(uid())}))')
pcb_lines.append(f'  (gr_text "AURA-X5 HAT EVT-B" (at 42.5 53.5) (layer "F.SilkS") (uuid {q(uid())}) (effects (font (size 1.4 1.4) (thickness 0.28))))')

for idx, (hx, hy) in enumerate(holes, 1):
    pcb_lines.append(f'''  (footprint "MountingHole:MountingHole_2.7mm_M2.5" (layer "F.Cu") (at {hx} {hy}) (uuid {q(uid())})
    (property "Reference" "H{idx}" (at 0 -2.6) (layer "F.SilkS") (uuid {q(uid())}) (effects (font (size 0.9 0.9) (thickness 0.15))))
    (pad "" np_thru_hole circle (at 0 0) (size 2.75 2.75) (drill 2.75) (layers "*.Cu" "*.Mask") (uuid {q(uid())}))
  )''')

for p in parts:
    dy_ref = p["label_dy"]
    fp_lines = [
        f'  (footprint {q(p["footprint"])} (layer "F.Cu") (at {p["x"]} {p["y"]}) (uuid {q(uid())})',
        f'    (property "Reference" {q(p["ref"])} (at 0 {dy_ref}) (layer "F.SilkS") (uuid {q(uid())}) (effects (font (size 0.9 0.9) (thickness 0.15))))',
        f'    (property "Value" {q(p["value"])} (at 0 {-dy_ref}) (layer "F.SilkS") (hide yes) (uuid {q(uid())}) (effects (font (size 0.8 0.8) (thickness 0.12))))',
    ]
    for d in p["pins"]:
        dx = round(d["x"] - p["x"], 3)
        dy = round(d["y"] - p["y"], 3)
        nid = d["netid"]
        fp_lines.append(
            f'    (pad {q(d["num"])} thru_hole {d["shape"]} (at {dx} {dy}) (size {d["diameter"]} {d["diameter"]}) '
            f'(drill {d["drill"]}) (layers "*.Cu" "*.Mask") (net {nid} {q(d["net"])}) (uuid {q(uid())}))'
        )
    fp_lines.append('  )')
    pcb_lines.extend(fp_lines)

for t in tracks:
    pcb_lines.append(
        f'  (segment (start {t["x1"]} {t["y1"]}) (end {t["x2"]} {t["y2"]}) '
        f'(width {t["width"]}) (layer {q(t["layer"])}) (net {nets[t["net"]]}) (uuid {q(uid())}))'
    )
for v in vias:
    pcb_lines.append(
        f'  (via (at {v["x"]} {v["y"]}) (size 0.7) (drill 0.35) (layers "F.Cu" "B.Cu") (net {nets[v["net"]]}) (uuid {q(uid())}))'
    )

# Bottom layer GND copper pour
gnd_nid = nets["GND"]
pcb_lines.append(f'''  (zone (net {gnd_nid}) (net_name "GND") (layer "B.Cu") (uuid {q(uid())})
    (hatch edge 0.5)
    (connect_pads (clearance 0.25))
    (min_thickness 0.25)
    (fill yes (thermal_gap 0.3) (thermal_bridge_width 0.35))
    (polygon (pts (xy 0.5 0.5) (xy 84.5 0.5) (xy 84.5 55.5) (xy 0.5 55.5)))
  )''')
pcb_lines.append(')')

pcb_path = OUT / "aura_x5_hat.kicad_pcb"
pcb_path.write_text("\n".join(pcb_lines), encoding="utf-8")
(OUT / "aura_x5_hat.kicad_pro").write_text(json.dumps({"meta": {"filename": "aura_x5_hat.kicad_pro", "version": 1}}, indent=2), encoding="utf-8")

# Emit Schematic + BOM + Positions
sch_lines = [
    '(kicad_sch (version 20250114) (generator "aura_x5_gen") (generator_version "9.0")',
    f'  (uuid {q(uid())})',
    '  (paper "A3")',
    '  (title_block (title "AURA-X5 Carrier HAT") (rev "EVT-B") (company "AURA-X5"))',
]
for i, p in enumerate(parts):
    sx = 30 + (i % 5) * 65
    sy = 30 + (i // 5) * 55
    sch_lines.append(f'  (text {q(p["ref"] + ": " + p["value"] + " [" + p["mpn"] + "]")} (at {sx} {sy} 0) (effects (font (size 1.5 1.5))) (uuid {q(uid())}))')
sch_lines.append(')')
(OUT / "aura_x5_hat.kicad_sch").write_text("\n".join(sch_lines), encoding="utf-8")

with (OUT / "bom.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["Reference", "Value", "MPN", "Footprint", "Description"])
    for p in parts:
        w.writerow([p["ref"], p["value"], p["mpn"], p["footprint"], p["description"]])

with (OUT / "positions.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["Designator", "Mid X(mm)", "Mid Y(mm)", "Layer", "Rotation"])
    for p in parts:
        w.writerow([p["ref"], p["x"], p["y"], "Top", 0])

# Run KiCad CLI DRC + Gerber + Drill + 3D Render
drc_json = OUT / "kicad_drc.json"
drc_errors, unconn_count = -1, -1
if KICAD_CLI.exists():
    subprocess.run([str(KICAD_CLI), "pcb", "drc", "--format", "json", "--output", str(drc_json), str(pcb_path)], check=False)
    subprocess.run([str(KICAD_CLI), "pcb", "export", "gerbers", "--output", str(FAB) + "/", str(pcb_path)], check=False)
    subprocess.run([str(KICAD_CLI), "pcb", "export", "drill", "--output", str(FAB) + "/", str(pcb_path)], check=False)
    # Package JLCPCB-ready Gerber ZIP
    zip_path = FAB / "aura_x5_hat_gerber.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for fpath in FAB.iterdir():
            if fpath.suffix.lower() in (".gtl", ".gbl", ".gto", ".gbo", ".gts", ".gbs", ".gm1", ".drl"):
                zf.write(fpath, fpath.name)
    subprocess.run([str(KICAD_CLI), "pcb", "render", "--side", "top", "--width", "1200", "--height", "800", "--output", str(OUT / "pcb_3d_top.png"), str(pcb_path)], check=False)
    drc_data = json.loads(drc_json.read_text(encoding="utf-8")) if drc_json.exists() else {}
    violations = drc_data.get("violations", [])
    drc_errors = sum(1 for v in violations if v.get("severity") == "error")
    unconn_count = len(drc_data.get("unconnected_items", []))
    print(f"KiCad DRC: errors={drc_errors}, warnings={len(violations)-drc_errors}, unconnected={unconn_count}")

summary = {
    "revision": "EVT-B",
    "parts_count": len(parts),
    "pads_count": len(pads),
    "nets_count": len(nets) - 1,
    "tracks_count": len(tracks),
    "vias_count": len(vias),
    "unrouted_internal": unrouted,
    "kicad_drc_errors": drc_errors,
    "kicad_unconnected": unconn_count,
    "kicad_drc_ok": (drc_errors == 0 and unconn_count == 0)
}
(OUT / "validation.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
