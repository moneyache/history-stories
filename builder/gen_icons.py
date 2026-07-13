# -*- coding: utf-8 -*-
"""Generate PWA icons for 上下五千年 — simple Chinese seal-style icon."""
import os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ICONS_DIR = os.path.join(os.path.dirname(HERE), "icons")


def draw_icon(size):
    """Draw a Chinese-inspired icon: red circular seal on parchment background."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background circle (parchment-color)
    r = size // 2
    margin = size // 16
    bg_r = r - margin

    # Parchment circle
    draw.ellipse(
        [margin, margin, size - margin, size - margin],
        fill=(253, 245, 220, 255),  # parchment-like
        outline=(180, 140, 80, 255),  # bronze/gold border
        width=max(3, size // 64),
    )

    # Inner red decorative ring
    inner_margin = size // 6
    draw.ellipse(
        [inner_margin, inner_margin, size - inner_margin, size - inner_margin],
        fill=None,
        outline=(192, 57, 43, 255),  # Chinese red
        width=max(2, size // 80),
    )

    # Center: draw simplified mountain/sun motif (Chinese landscape)
    cx, cy = size // 2, size // 2
    s = size // 3  # scale factor

    # Sun (red circle, upper-center)
    sun_r = size // 8
    sun_y = cy - size // 8
    draw.ellipse(
        [cx - sun_r, sun_y - sun_r, cx + sun_r, sun_y + sun_r],
        fill=(220, 60, 40, 255),
    )

    # Mountains (two peaks)
    # Left mountain (larger)
    mt1_left = cx - s
    mt1_right = cx + s // 6
    mt1_top = cy - s // 8
    mt1_bottom = cy + s // 2
    draw.polygon(
        [
            (mt1_left, mt1_bottom),  # bottom-left
            (cx - s // 3, mt1_top),  # peak
            (mt1_right, mt1_bottom),  # bottom-right
        ],
        fill=(139, 100, 60, 255),  # mountain brown
    )

    # Right mountain (smaller, overlapping)
    mt2_left = cx - s // 8
    mt2_right = cx + s
    mt2_top = cy + s // 6
    mt2_bottom = cy + s // 2
    draw.polygon(
        [
            (mt2_left, mt2_bottom),
            (cx + s // 3, mt2_top),  # peak
            (mt2_right, mt2_bottom),
        ],
        fill=(120, 80, 50, 255),
    )

    # River/water line at bottom
    water_y = cy + s // 3
    draw.arc(
        [cx - s // 2, water_y, cx + s // 2, water_y + s // 3],
        start=0, end=180,
        fill=(100, 140, 180, 255),
        width=max(2, size // 50),
    )

    return img


def main():
    os.makedirs(ICONS_DIR, exist_ok=True)

    for size in [192, 512]:
        img = draw_icon(size)
        path = os.path.join(ICONS_DIR, f"icon-{size}.png")
        img.save(path, "PNG")
        print(f"  ✓ {path} ({size}x{size})")


if __name__ == "__main__":
    main()
