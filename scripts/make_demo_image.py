"""Draw the web app's demo picture (web/static/demo.png): a lit sphere and a ring over a chequered floor.

Everything is computed here (no photo or third-party image), so the demo is reproducible:
    python scripts/make_demo_image.py
"""
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "web" / "static" / "demo.png"
W, H = 360, 240
LIGHT = np.array([-0.5, -0.6, 0.62])
LIGHT = LIGHT / np.linalg.norm(LIGHT)


def render():
    y, x = np.mgrid[0:H, 0:W].astype(float)
    horizon = H * 0.62
    # sky: dark blue at the top to a warm glow at the horizon
    t = np.clip(y / horizon, 0, 1)[..., None]
    img = (1 - t) * np.array([12, 18, 48]) + t * np.array([235, 150, 90])
    # floor: chequerboard in perspective, fading into the distance
    floor = y > horizon
    depth = 40.0 / np.maximum(y - horizon, 1e-3)
    u, v = (x - W / 2) * depth / 18.0, depth * 3.0
    cheq = ((np.floor(u) + np.floor(v)) % 2 == 0)
    fade = np.clip((y - horizon) / (H - horizon), 0, 1)[..., None] ** 0.6
    tiles = np.where(cheq[..., None], [225, 225, 215], [40, 45, 60]) * fade + (1 - fade) * np.array([170, 120, 90])
    img[floor] = tiles[floor]
    # shadow of the sphere on the floor
    shadow = ((x - W * 0.45) / 70) ** 2 + ((y - H * 0.86) / 12) ** 2
    img *= (1 - 0.55 * np.exp(-shadow * 1.5) * floor)[..., None]
    # sphere with diffuse + specular shading
    cx, cy, r = W * 0.42, H * 0.52, H * 0.3
    dx, dy = (x - cx) / r, (y - cy) / r
    inside = dx ** 2 + dy ** 2 < 1
    dz = np.sqrt(np.clip(1 - dx ** 2 - dy ** 2, 0, 1))
    lam = np.clip(dx * LIGHT[0] + dy * LIGHT[1] + dz * LIGHT[2], 0, 1)
    spec = lam ** 40
    sphere = (0.12 + 0.88 * lam)[..., None] * np.array([70, 200, 235]) + spec[..., None] * 255
    img[inside] = sphere[inside]
    # ring to the right, lit from the same side
    rx, ry = (x - W * 0.8) / 34, (y - H * 0.36) / 34
    rr = np.sqrt(rx ** 2 + ry ** 2)
    ring = np.abs(rr - 1) < 0.28
    shade = 0.45 + 0.55 * np.clip(-(rx * 0.6 + ry * 0.8) / np.maximum(rr, 1e-6), 0, 1)
    img[ring] = (shade[..., None] * np.array([255, 205, 70]))[ring]
    return Image.fromarray(np.clip(img, 0, 255).round().astype(np.uint8), "RGB")


if __name__ == "__main__":
    render().save(OUT, optimize=True)
    print(f"{OUT.relative_to(ROOT)}: {OUT.stat().st_size / 1024:.0f} KB")
