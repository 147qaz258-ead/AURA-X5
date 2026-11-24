"""Parametric 3D CAD generator for AURA-X5 Desktop Embodied Agent Console (EVT-B).
Uses CadQuery 2.8.0 + trimesh.
Enclosed 18-deg tilted desktop console with:
- Side cheeks & 4x M3 mounting bosses mating front_console to base_shell
- RDK X5 58x49mm M2.5 standoffs + rear I/O ports + bottom intake louvers
- Top-rear 30x30x7mm 5V PWM cooling fan mount (24x24mm M3 pattern + D28mm exhaust)
- 3.5inch RPi Display (480x320, ILI9486+XPT2046) pocket & 74.2x49.8mm touch window
- DPDT Privacy Switch, Red LED, Mic pinhole, Kill-Switch, EC11 Encoder + Knob
"""
from pathlib import Path
import json
import math
import cadquery as cq
import trimesh

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "mechanical"
PRINT_DIR = OUT / "print"
OUT.mkdir(parents=True, exist_ok=True)
PRINT_DIR.mkdir(parents=True, exist_ok=True)

WALL = 2.4
BASE_W = 104.0   # X
BASE_D = 114.0   # Y
BASE_H_REAR = 46.0
BASE_H_FRONT = 22.0
BEZEL_W = BASE_W
BEZEL_H = 90.0
BEZEL_T = 4.0
TILT_DEG = 18.0  # Tilted back 18 deg from vertical? No, 18 deg from horizontal? Wait: 68 deg from horizontal = 22 deg from vertical; let's use 55 deg console angle!
CONSOLE_ANGLE = 55.0  # 55 deg from horizontal (35 deg ergonomic tilt back)

# 1. Enclosed Base Shell with Sloped Front Profile
# Side profile in YZ plane: bottom (y=-57..+57, z=0), rear wall (y=+57, z=0..46), top rear deck (y=+10..+57, z=46), sloped front opening
# Built as solid shell then shelled/cut inside for clean 3D printability
side_pts = [
    (-BASE_D / 2, 0.0),
    (BASE_D / 2, 0.0),
    (BASE_D / 2, BASE_H_REAR),
    (-2.0, BASE_H_REAR),
    (-BASE_D / 2, BASE_H_FRONT),
]
base_outer = (
    cq.Workplane("YZ")
    .polyline(side_pts)
    .close()
    .extrude(BASE_W / 2, both=True)
    .edges("|X")
    .fillet(3.0)
)
inner_pts = [
    (-BASE_D / 2 + WALL, WALL),
    (BASE_D / 2 - WALL, WALL),
    (BASE_D / 2 - WALL, BASE_H_REAR - WALL),
    (-2.0, BASE_H_REAR - WALL),
    (-BASE_D / 2 + WALL, BASE_H_FRONT),
]
base_inner = (
    cq.Workplane("YZ")
    .polyline(inner_pts)
    .close()
    .extrude(BASE_W / 2 - WALL, both=True)
)
base_shell = base_outer.cut(base_inner)

# Open the sloped front face so the front console mounts flush onto the sloped rim
# Normal of sloped face goes from (-2, 46) to (-57, 22): dy=-55, dz=-24 -> length ~60mm, wait: let's make sloped face length = 90mm!
# Let's cut a clean front access opening through the sloped front wall
front_open = (
    cq.Workplane("YZ")
    .polyline([(-BASE_D / 2 - 2, BASE_H_FRONT - 2), (-2.0, BASE_H_REAR + 2), (-10.0, BASE_H_REAR - 6), (-BASE_D / 2 + 4, BASE_H_FRONT - 6)])
    .close()
    .extrude(BASE_W / 2 - WALL * 2, both=True)
)
base_shell = base_shell.cut(front_open)

# Rear I/O cutouts (Y = +BASE_D/2) for RDK X5 Ethernet, USB 3.0, HDMI, USB-C Power/OTG
rear_io = (
    cq.Workplane("XZ")
    .workplane(offset=BASE_D / 2)
    .center(0, WALL + 13.0)
    .rect(78.0, 20.0)
    .extrude(WALL * 3, both=True)
)
base_shell = base_shell.cut(rear_io)

# Bottom intake louvers
for i in range(-3, 4):
    slot = cq.Workplane("XY").center(i * 10.0, 14.0).rect(4.0, 44.0).extrude(WALL * 2, both=True)
    base_shell = base_shell.cut(slot)

# Top-rear 30x30x7mm Cooling Fan Mount (centered at X=0, Y=+30, Z=BASE_H_REAR)
fan_hole = cq.Workplane("XY").workplane(offset=BASE_H_REAR).center(0, 28.0).circle(14.0).extrude(WALL * 3, both=True)
base_shell = base_shell.cut(fan_hole)
for fx in (-12.0, 12.0):
    for fy in (16.0, 40.0):
        f_scr = cq.Workplane("XY").workplane(offset=BASE_H_REAR).center(fx, fy).circle(1.6).extrude(WALL * 3, both=True)
        base_shell = base_shell.cut(f_scr)

# 4x M2.5 Standoffs for RDK X5 (58mm x 49mm hole pattern, rear bay Y=+22mm)
rdk_y_offset = 22.0
for sx in (-29.0, 29.0):
    for sy in (-24.5, 24.5):
        standoff = cq.Workplane("XY").workplane(offset=WALL).center(sx, rdk_y_offset + sy).circle(3.2).extrude(6.0)
        hole = cq.Workplane("XY").workplane(offset=WALL).center(sx, rdk_y_offset + sy).circle(1.25).extrude(7.0)
        base_shell = base_shell.union(standoff).cut(hole)

# 4x M3 Mounting Bosses inside front corners for Front Console
for bx in (-BASE_W / 2 + 7.0, BASE_W / 2 - 7.0):
    for by, bz in [(-BASE_D / 2 + 8.0, BASE_H_FRONT - 2.0), (-6.0, BASE_H_REAR - 6.0)]:
        boss = cq.Workplane("XY").workplane(offset=bz - 6.0).center(bx, by).circle(3.5).extrude(6.0)
        b_hole = cq.Workplane("XY").workplane(offset=bz - 6.0).center(bx, by).circle(1.45).extrude(7.0)
        base_shell = base_shell.union(boss).cut(b_hole)

# 2. Front 3.5" Touch Console Plate (flat for optimal 3D printing, bolts onto sloped front)
bezel = (
    cq.Workplane("XY")
    .box(BEZEL_W, BEZEL_H, BEZEL_T, centered=(True, True, False))
    .edges("|Z")
    .fillet(5.0)
)
# 3.5" Active Display Window (74.2 x 49.8 mm)
bezel = bezel.cut(cq.Workplane("XY").center(0, 14.0).rect(74.2, 49.8).extrude(BEZEL_T * 2, both=True))
# Backside PCB Pocket (86.2 x 56.4 mm)
bezel = bezel.cut(cq.Workplane("XY").center(0, 14.0).rect(86.2, 56.4).extrude(1.8))
# Front Controls: Privacy DPDT, Red LED, Mic, Kill-Switch, EC11
bezel = bezel.cut(cq.Workplane("XY").center(-32.0, -24.0).rect(6.5, 12.5).extrude(BEZEL_T * 2, both=True))
bezel = bezel.cut(cq.Workplane("XY").center(-22.0, -24.0).circle(1.65).extrude(BEZEL_T * 2, both=True))
bezel = bezel.cut(cq.Workplane("XY").center(-12.0, -24.0).circle(1.5).extrude(BEZEL_T * 2, both=True))
bezel = bezel.cut(cq.Workplane("XY").center(0.0, -24.0).circle(6.1).extrude(BEZEL_T * 2, both=True))
bezel = bezel.cut(cq.Workplane("XY").center(30.0, -24.0).circle(3.6).extrude(BEZEL_T * 2, both=True))
# 4x M3 Corner Screw Holes
for mx in (-BEZEL_W / 2 + 7.0, BEZEL_W / 2 - 7.0):
    for my in (-BEZEL_H / 2 + 7.0, BEZEL_H / 2 - 7.0):
        bezel = bezel.cut(cq.Workplane("XY").center(mx, my).circle(1.65).extrude(BEZEL_T * 2, both=True))

# 3. Knurled EC11 Rotary Encoder Knob
knob = cq.Workplane("XY").circle(12.0).extrude(14.0).faces(">Z").chamfer(1.2)
knob = knob.cut(cq.Workplane("XY").circle(3.05).extrude(10.0))

# Position assembly for STEP export
slope_deg = math.degrees(math.atan2(BASE_H_REAR - BASE_H_FRONT, BASE_D / 2 - 2.0))
bezel_pos = bezel.rotate((0, 0, 0), (1, 0, 0), slope_deg).translate((0, -BASE_D / 4 - 2.0, (BASE_H_FRONT + BASE_H_REAR) / 2))

assembly = cq.Assembly()
assembly.add(base_shell, name="base_shell", color=cq.Color(0.15, 0.16, 0.19, 1.0))
assembly.add(bezel_pos, name="front_console", color=cq.Color(0.24, 0.27, 0.31, 1.0))
assembly.add(knob.translate((30.0, -BASE_D / 2 + 12.0, BASE_H_FRONT + 4.0)), name="encoder_knob", color=cq.Color(0.85, 0.35, 0.15, 1.0))

assembly.save(str(OUT / "assembly.step"))
cq.exporters.export(base_shell, str(PRINT_DIR / "base_shell.stl"))
cq.exporters.export(bezel, str(PRINT_DIR / "front_console_flat.stl"))
cq.exporters.export(knob, str(PRINT_DIR / "encoder_knob.stl"))

fit_report = {}
for name, stl_path in [
    ("base_shell", PRINT_DIR / "base_shell.stl"),
    ("front_console_flat", PRINT_DIR / "front_console_flat.stl"),
    ("encoder_knob", PRINT_DIR / "encoder_knob.stl"),
]:
    mesh = trimesh.load(str(stl_path))
    fit_report[name] = {
        "watertight": bool(mesh.is_watertight),
        "volume_cm3": round(float(mesh.volume) / 1000.0, 2),
        "bounds_mm": [round(float(x), 2) for x in mesh.extents],
    }

(OUT / "fit_check.json").write_text(json.dumps(fit_report, indent=2), encoding="utf-8")
print(json.dumps(fit_report, indent=2))
