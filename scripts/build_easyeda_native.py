"""Build AURA-X5 HAT natively in running EasyEDA Pro via easyeda-api-skill bridge.
Phase A: Clear Schematic1, place all 32 LCSC components, wire all 36 nets, and push to PCB1.
"""
import json
import urllib.request

BRIDGE = "http://localhost:49620"
LIB_UUID = "0819f05c4eef4c71ace90d822a990e87"

DEVICES = {
    "H2X20": "b17ff5dacafd4dfeafdb2e8e12f1cbaf",   # 2x20P 2.54mm Female Header
    "H2X13": "59750614f4614c6b9b1d597c511998ea",   # 2x13P 2.54mm Header
    "H2X3":  "04169766c4244014b6b802721a9d667a",   # 2x3P 2.54mm Header
    "H1X4":  "03f2d26dc66a4070bdf551926e792598",   # 1x4P 2.54mm Header
    "H1X7":  "1fc8cb3d16c941ffa134d70e2a85859d",   # 1x7P 2.54mm Header
    "H1X5":  "c8ade3d632234d6d8115ad343498eb8e",   # 1x5P 2.54mm Header
    "H1X3":  "8c5282bb0a03497ca34b12735e6b8dae",   # 1x3P 2.54mm Header
    "H1X2":  "99b1039acd624894acb0c01cac9f07f5",   # 1x2P 2.54mm Header
    "LDO33": "9f9c6cb41c7449fd8acf96aceed2661a",   # AMS1117-3.3 SOT-223
    "PTC":   "7d446e0761084cf8a4d85ccd46ae110d",   # SMD0805-110 PTC Fuse
    "TVS":   "833f26bbbaec4a5fb2fd0c80f9a1312e",   # SMBJ5.0A SMB
    "NPN":   "e84258a7c4c54ed6b903438d47c3f671",   # MMBT3904 SOT-23
    "NMOS":  "f8007837564a4f1fa0e6b57b81dccb0d",   # 2N7002 SOT-23
    "LED_R": "044668f4d8a64015bfbf32f95a0f5c4c",   # KT-0603R Red LED
    "D1N4148":"b1fbc6c9168c437ab79ee93b712a902c",  # 1N4148WS SOD-323
    "R1K":   "18db11499a04403ba8c98e2f7a687fbc",   # 1k 0603
    "R10K":  "b948db94476e4027ac8953235755ec96",   # 10k 0603
    "C10U":  "8c1f4a9e9d204b148b36ce719c891bd1",   # 10uF 0805
    "C100N": "96b39256cc3f4d80bd3b503deb4f3328",   # 100nF 0603
}

RDK_PIN_NETS = {
    "1": "+3V3_RDK", "2": "VBUS_5V", "3": "I2C_SDA", "4": "VBUS_5V", "5": "I2C_SCL",
    "6": "GND", "7": "KILL_SW", "8": "UART_TX", "9": "GND", "10": "UART_RX",
    "11": "TP_IRQ", "12": "I2S_BCLK", "13": "EC11_A", "14": "GND", "15": "EC11_B",
    "16": "EC11_SW", "17": "+3V3_RDK", "18": "LCD_RS", "19": "SPI_MOSI", "20": "GND",
    "21": "SPI_MISO", "22": "LCD_RST", "23": "SPI_SCK", "24": "LCD_CS", "25": "GND",
    "26": "TP_CS", "29": "PRIV_SENSE", "30": "GND",
    "31": "BUZZ_PWM", "32": "FAN_PWM", "33": "WS2812_3V3", "34": "GND", "35": "I2S_LRCLK",
    "38": "I2S_DIN", "39": "GND", "40": "I2S_DOUT"
}
J2_ACTIVE = {1, 2, 4, 6, 9, 11, 14, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26}
J2_NETS = {str(p): RDK_PIN_NETS[str(p)] for p in J2_ACTIVE}

# Component list: (ref, dev_key, sch_x, sch_y, pin_net_map)
COMPONENTS = [
    ("J1", "H2X20", 200, 350, RDK_PIN_NETS),
    ("J2", "H2X13", 430, 350, J2_NETS),
    ("F1", "PTC", 650, 150, {"1": "VBUS_5V", "2": "V5_PROT"}),
    ("D1", "TVS", 760, 150, {"1": "V5_PROT", "2": "GND"}),
    ("U1", "LDO33", 880, 150, {"1": "GND", "2": "+3V3_EXT", "3": "V5_PROT", "4": "+3V3_EXT"}),
    ("C1", "C10U", 650, 230, {"1": "V5_PROT", "2": "GND"}),
    ("C2", "C10U", 760, 230, {"1": "+3V3_EXT", "2": "GND"}),
    ("C3", "C100N", 880, 230, {"1": "+3V3_EXT", "2": "GND"}),

    ("J3", "H2X3", 650, 330, {"1": "+3V3_EXT", "2": "V_PRIVACY_3V3", "3": "GND", "4": "+3V3_EXT", "5": "PRIV_SENSE", "6": "GND"}),
    ("R1", "R1K", 780, 330, {"1": "V_PRIVACY_3V3", "2": "LED_PRIV_A"}),
    ("D2", "LED_R", 900, 330, {"1": "GND", "2": "LED_PRIV_A"}),

    ("J4", "H1X4", 650, 440, {"1": "GND", "2": "+3V3_EXT", "3": "I2C_SDA", "4": "I2C_SCL"}),
    ("J5", "H1X4", 780, 440, {"1": "V5_PROT", "2": "GND", "3": "UART_TX", "4": "UART_RX"}),
    ("J6", "H1X7", 920, 440, {"1": "V_PRIVACY_3V3", "2": "V5_PROT", "3": "GND", "4": "I2S_BCLK", "5": "I2S_LRCLK", "6": "I2S_DIN", "7": "I2S_DOUT"}),

    ("J7", "H1X5", 200, 620, {"1": "GND", "2": "+3V3_EXT", "3": "EC11_A", "4": "EC11_B", "5": "EC11_SW"}),
    ("R6", "R10K", 330, 600, {"1": "+3V3_EXT", "2": "EC11_A"}),
    ("R7", "R10K", 330, 660, {"1": "+3V3_EXT", "2": "EC11_B"}),
    ("C5", "C100N", 440, 600, {"1": "EC11_A", "2": "GND"}),
    ("C6", "C100N", 440, 660, {"1": "EC11_B", "2": "GND"}),

    ("J8", "H1X2", 560, 600, {"1": "GND", "2": "KILL_SW"}),
    ("R2", "R10K", 660, 600, {"1": "+3V3_EXT", "2": "KILL_SW"}),
    ("C4", "C100N", 760, 600, {"1": "KILL_SW", "2": "GND"}),

    ("Q3", "NMOS", 560, 700, {"1": "+3V3_EXT", "2": "WS2812_3V3", "3": "WS2812_5V"}),
    ("R8", "R1K", 680, 700, {"1": "V5_PROT", "2": "WS2812_5V"}),
    ("J9", "H1X3", 800, 700, {"1": "V5_PROT", "2": "GND", "3": "WS2812_5V"}),

    ("R3", "R1K", 920, 600, {"1": "FAN_PWM", "2": "FAN_BASE"}),
    ("Q1", "NPN", 1020, 600, {"1": "FAN_BASE", "2": "GND", "3": "FAN_L"}),
    ("D3", "D1N4148", 1020, 660, {"1": "FAN_L", "2": "V5_PROT"}),
    ("J10", "H1X2", 1120, 600, {"1": "V5_PROT", "2": "FAN_L"}),

    ("R4", "R1K", 920, 720, {"1": "BUZZ_PWM", "2": "BUZZ_BASE"}),
    ("Q2", "NPN", 1020, 720, {"1": "BUZZ_BASE", "2": "GND", "3": "BUZZ_L"}),
    ("J11", "H1X2", 1120, 720, {"1": "V5_PROT", "2": "BUZZ_L"}),
]


def exe(code: str, timeout: int = 60):
    req = urllib.request.Request(
        f"{BRIDGE}/execute",
        data=json.dumps({"code": code}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code}: {body}") from e
    if not data.get("success"):
        raise RuntimeError(f"EasyEDA error: {data}")
    return data.get("result")


def main():
    # 1. Clear existing test items on Schematic1 P1
    clear_js = """
    const pages = await eda.dmt_Schematic.getAllSchematicPagesInfo();
    await eda.dmt_EditorControl.openDocument(pages[0].uuid);
    const wires = await eda.sch_PrimitiveWire.getAllPrimitiveId();
    if (wires && wires.length) await eda.sch_PrimitiveWire.delete(wires);
    const comps = await eda.sch_PrimitiveComponent.getAll();
    const ids = (comps || []).map(c => c.primitiveId).filter(Boolean);
    if (ids.length) await eda.sch_PrimitiveComponent.delete(ids);
    return { clearedWires: wires ? wires.length : 0, clearedComps: ids.length };
    """
    print("Clear Schematic1:", exe(clear_js))

    # 2. Place all 32 components and wire every pin in batches of 4
    spec = [
        {"ref": ref, "uuid": DEVICES[dk], "x": sx, "y": sy, "pins": pmap}
        for ref, dk, sx, sy, pmap in COMPONENTS
    ]
    all_res = []
    for i in range(0, len(spec), 4):
        batch = spec[i:i+4]
        place_js = f"""
        const lib = "{LIB_UUID}";
        const specs = {json.dumps(batch)};
        const placed = [];
        for (const s of specs) {{
          const comp = await eda.sch_PrimitiveComponent.create({{ libraryUuid: lib, uuid: s.uuid }}, s.x, s.y);
          const pid = comp.getState_PrimitiveId();
          await eda.sch_PrimitiveComponent.modify(pid, {{ designator: s.ref }});
          const pins = await eda.sch_PrimitiveComponent.getAllPinsByPrimitiveId(pid);
          let wired = 0;
          for (const pin of pins) {{
            const netName = s.pins[String(pin.pinNumber)];
            if (!netName) continue;
            const rot = Number(pin.rotation || 0) % 360;
            let dx = 0, dy = 0;
            if (rot === 0) dx = 20;
            else if (rot === 180) dx = -20;
            else if (rot === 90) dy = -20;
            else if (rot === 270) dy = 20;
            else dx = -20;
            await eda.sch_PrimitiveWire.create([pin.x, pin.y, pin.x + dx, pin.y + dy], netName);
            wired++;
          }}
          placed.push({{ ref: s.ref, pid, pins: pins.length, wired }});
        }}
        return placed;
        """
        res = exe(place_js, timeout=60)
        all_res.extend(res)
        for r in res:
            print(f"  {r['ref']}: {r['wired']}/{r['pins']} pins wired")
    exe("await eda.sch_Document.save(); return true;")
    print(f"Total placed & saved: {len(all_res)} components.")


if __name__ == "__main__":
    main()
