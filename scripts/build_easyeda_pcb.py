"""Complete PCB1 layout, 85x56mm outline, mounting holes, GND pour, and auto-routing in EasyEDA Pro."""
import json
import urllib.request

BRIDGE = "http://localhost:49620"
MIL = 39.37007874  # 1 mm in mil

def mm(v):
    return round(v * MIL, 2)

def exe(code: str, timeout: int = 120):
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


# Layout in mm (origin bottom-left (0,0), Y+ up, board 85 x 56 mm)
# RDK X5 40-pin center at (32.5, 52.5), MH1=(3.5,3.5), MH2=(61.5,3.5), MH3=(3.5,52.5), MH4=(61.5,52.5)
PLACEMENT_MM = {
    "J1":  (32.5, 52.5, 0),
    "J2":  (26.0, 39.0, 0),
    "F1":  (74.0, 48.0, 0),
    "D1":  (74.0, 42.0, 0),
    "U1":  (74.0, 35.0, 0),
    "C1":  (65.0, 42.0, 0),
    "C2":  (65.0, 36.0, 0),
    "C3":  (65.0, 31.0, 0),

    "J4":  (10.0, 27.0, 0),
    "J5":  (24.0, 27.0, 0),
    "J6":  (42.0, 27.0, 0),

    "R1":  (10.0, 18.0, 0),
    "D2":  (20.0, 18.0, 0),
    "J3":  (10.0, 9.0,  0),

    "R6":  (31.0, 20.0, 0),
    "R7":  (31.0, 15.0, 0),
    "C5":  (40.0, 20.0, 0),
    "C6":  (40.0, 15.0, 0),
    "J7":  (23.0, 9.0,  0),

    "J8":  (38.0, 9.0,  0),
    "R2":  (49.0, 20.0, 0),
    "C4":  (49.0, 15.0, 0),

    "Q3":  (59.0, 20.0, 0),
    "R8":  (59.0, 14.0, 0),
    "J9":  (48.0, 9.0,  0),

    "R3":  (69.0, 22.0, 0),
    "Q1":  (71.0, 16.0, 0),
    "D3":  (72.0, 27.0, 0),
    "J10": (68.0, 9.0,  0),

    "R4":  (79.0, 22.0, 0),
    "Q2":  (80.0, 16.0, 0),
    "J11": (77.0, 9.0,  0),
}

HOLES_MM = [(3.5, 3.5), (61.5, 3.5), (3.5, 52.5), (61.5, 52.5)]


def main():
    W, H = mm(85.0), mm(56.0)
    placement_mil = {k: [mm(x), mm(y), rot] for k, (x, y, rot) in PLACEMENT_MM.items()}
    holes_mil = [[mm(x), mm(y)] for x, y in HOLES_MM]

    setup_js = f"""
    const W = {W}, H = {H};
    const oldLines = await eda.pcb_PrimitivePolyline.getAll(undefined, 11);
    if (oldLines && oldLines.length) await eda.pcb_PrimitivePolyline.delete(oldLines.map(x => x.primitiveId));
    const outlinePoly = eda.pcb_MathPolygon.createPolygon([0, 0, 'L', W, 0, W, H, 0, H, 0, 0]);
    await eda.pcb_PrimitivePolyline.create('', 11, outlinePoly, 8);

    const holes = {json.dumps(holes_mil)};
    for (let i = 0; i < holes.length; i++) {{
      const [hx, hy] = holes[i];
      await eda.pcb_PrimitivePad.create(12, 'H' + (i + 1), hx, hy, 0, ['ELLIPSE', 180, 180], '', ['ROUND', 110], 0, 0, 0, false, 0);
    }}

    const posMap = {json.dumps(placement_mil)};
    const comps = await eda.pcb_PrimitiveComponent.getAll();
    let moved = 0;
    for (const c of comps) {{
      const target = posMap[c.designator];
      if (!target) continue;
      await eda.pcb_PrimitiveComponent.modify(c.primitiveId, {{ x: target[0], y: target[1], rotation: target[2] }});
      moved++;
    }}

    const pourPoly = eda.pcb_MathPolygon.createPolygon([20, 20, 'L', W - 20, 20, W - 20, H - 20, 20, H - 20, 20, 20]);
    await eda.pcb_PrimitivePour.create('GND', 2, pourPoly);
    await eda.pcb_Document.save();
    return {{ moved, totalComps: comps.length }};
    """
    print("Board setup & placement:", exe(setup_js))

    print("Running EasyEDA native autoRouting...")
    route_js = """
    const res = await eda.pcb_Document.autoRouting();
    await eda.pcb_Document.save();
    const drcOk = await eda.pcb_Drc.check(false, false, false);
    return { route: res, drcOk };
    """
    print("AutoRouting & DRC:", exe(route_js, timeout=180))


if __name__ == "__main__":
    main()
