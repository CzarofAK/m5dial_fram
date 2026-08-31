#!/usr/bin/env python3
"""Generate warning_1.png / warning_2.png -- the two-frame blocky
pixel-art warning triangle used by overlay_preflight.yaml's animimg
widget (a pulse between amber and white/red, not a real animated GIF
-- LVGL just alternates the two static images, same technique as
overlay_litterbox.yaml's cat, see m5dial_pages/assets/gen_cat.py).

Re-run this (`pip install pillow && python3 gen_warning.py`) after
editing the shape/colors below; don't hand-edit the PNGs
pixel-by-pixel. Requires Pillow. Output is RGBA with a real alpha
channel (background alpha 0) -- rendered with `transparency:
alpha_channel` in ESPHome (real per-pixel alpha), not `chroma_key` --
see overlay_litterbox.yaml's header for why chroma_key was dropped.
"""

from pathlib import Path

from PIL import Image

BLOCK = 8  # scale factor: one grid cell -> BLOCK x BLOCK real pixels
GRID = 16
SIZE = GRID * BLOCK

OUTLINE = (25, 20, 10, 255)


def triangle_cells() -> set[tuple[int, int]]:
    """Grid (row, col) cells covered by the triangle, apex at the top."""
    cells = set()
    apex_row, base_row = 1, 13
    for r in range(apex_row, base_row + 1):
        t = (r - apex_row) / (base_row - apex_row)  # 0..1
        half = t * 7.2
        left = round(7.5 - half)
        right = round(7.5 + half)
        for c in range(left, right + 1):
            cells.add((r, c))
    return cells


def render(fill: tuple[int, int, int, int], exclaim_color: tuple[int, int, int, int], path: Path) -> None:
    tri = triangle_cells()
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    px = img.load()

    def paint_cell(r: int, c: int, color: tuple[int, int, int, int]) -> None:
        for by in range(BLOCK):
            for bx in range(BLOCK):
                px[c * BLOCK + bx, r * BLOCK + by] = color

    for r, c in tri:
        paint_cell(r, c, fill)
    # Outline: any triangle cell with a non-triangle neighbor.
    for r, c in tri:
        neighbors = [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]
        if any(n not in tri for n in neighbors):
            paint_cell(r, c, OUTLINE)
    # Exclamation mark: stem + dot, centered.
    for r in range(4, 10):
        for c in (7, 8):
            paint_cell(r, c, exclaim_color)
    for r in (11, 12):
        for c in (7, 8):
            paint_cell(r, c, exclaim_color)

    img.save(path)


if __name__ == "__main__":
    here = Path(__file__).parent
    # Frame 1: amber triangle, dark exclamation mark.
    render((243, 156, 18, 255), OUTLINE, here / "warning_1.png")
    # Frame 2: white triangle, red exclamation mark -- the pulse.
    render((255, 255, 255, 255), (231, 76, 60, 255), here / "warning_2.png")
    print("wrote warning_1.png, warning_2.png")
