"""Generate PWA app icons for Bishwa Medicare Sales Tracker.
Run once: python generate_icons.py
Creates static/icons/icon-192.png and static/icons/icon-512.png
No external dependencies — pure Python stdlib.
"""
import math, os, struct, zlib

OUT_DIR = os.path.join(os.path.dirname(__file__), "static", "icons")
os.makedirs(OUT_DIR, exist_ok=True)


def _write_png(path, size, pixel_fn):
    raw = bytearray()
    for y in range(size):
        raw.append(0)  # filter type: None
        for x in range(size):
            raw.extend(pixel_fn(x, y))

    def chunk(tag, data):
        body = tag + data
        return (struct.pack(">I", len(data)) + body +
                struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF))

    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)))
        f.write(chunk(b"IDAT", zlib.compress(bytes(raw), 9)))
        f.write(chunk(b"IEND", b""))


def _lerp(a, b, t):
    return int(a + (b - a) * max(0.0, min(1.0, t)))


def _icon_pixel(x, y, S):
    cx = cy = (S - 1) / 2.0

    # Rounded-rect corner clip (radius ~22% of size)
    r = S * 0.22
    px = max(r - x, 0.0, x - (S - 1 - r))
    py = max(r - y, 0.0, y - (S - 1 - r))
    if px > 0 and py > 0 and px * px + py * py > r * r:
        return (248, 250, 252)  # light page background outside rounded rect

    # Diagonal gradient: purple #4F46E5 → teal #0EA5A4
    t = (x + y) / (2.0 * (S - 1))
    bg = (
        _lerp(0x4F, 0x0E, t),
        _lerp(0x46, 0xA5, t),
        _lerp(0xE5, 0xA4, t),
    )

    # White diamond (L1 distance from centre ≤ 30% of half-size)
    diamond_r = S * 0.30
    if abs(x - cx) + abs(y - cy) <= diamond_r:
        # Teal centre circle inside the diamond
        if math.hypot(x - cx, y - cy) <= S * 0.10:
            return (14, 165, 164)   # #0EA5A4
        return (255, 255, 255)      # white diamond body

    return bg


for size, name in [(192, "icon-192.png"), (512, "icon-512.png")]:
    dest = os.path.join(OUT_DIR, name)
    _write_png(dest, size, lambda x, y, S=size: _icon_pixel(x, y, S))
    print(f"  {dest}  ({size}x{size})")

print("Done.")
