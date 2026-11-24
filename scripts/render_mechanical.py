"""Render multi-view 3D preview of AURA-X5 mechanical STL parts using trimesh + matplotlib."""
from pathlib import Path
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

ROOT = Path(__file__).resolve().parents[1]
PRINT_DIR = ROOT / "mechanical" / "print"
OUT_IMG = ROOT / "mechanical" / "cad_preview.png"

parts = [
    ("Base Shell (104x112x34mm)", PRINT_DIR / "base_shell.stl", (0.20, 0.25, 0.32, 0.85)),
    ("Front 3.5\" Touch Console (104x92x4mm)", PRINT_DIR / "front_console_flat.stl", (0.30, 0.36, 0.44, 0.90)),
    ("EC11 Encoder Knob (D24x14mm)", PRINT_DIR / "encoder_knob.stl", (0.85, 0.38, 0.16, 0.95)),
]

fig = plt.figure(figsize=(15, 5), dpi=140)
fig.patch.set_facecolor("#111418")

for idx, (title, stl_path, color) in enumerate(parts, 1):
    mesh = trimesh.load(str(stl_path))
    ax = fig.add_subplot(1, 3, idx, projection="3d")
    ax.set_facecolor("#111418")
    # Subsample faces if very dense so render stays fast and crisp
    faces = mesh.faces
    if len(faces) > 6000:
        step = max(1, len(faces) // 6000)
        faces = faces[::step]
    tris = mesh.vertices[faces]
    coll = Poly3DCollection(tris, facecolors=color, edgecolors=(0.08, 0.10, 0.12, 0.25), linewidths=0.2)
    ax.add_collection3d(coll)
    bounds = mesh.bounds
    center = (bounds[0] + bounds[1]) / 2.0
    span = float(np.max(bounds[1] - bounds[0])) * 0.62
    ax.set_xlim(center[0] - span, center[0] + span)
    ax.set_ylim(center[1] - span, center[1] + span)
    ax.set_zlim(center[2] - span, center[2] + span)
    ax.view_init(elev=28, azim=-48)
    ax.set_title(title, color="white", fontsize=11, pad=10)
    ax.set_axis_off()

plt.tight_layout()
plt.savefig(str(OUT_IMG), facecolor=fig.get_facecolor(), bbox_inches="tight")
print(f"Saved {OUT_IMG}")
