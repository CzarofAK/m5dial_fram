#!/usr/bin/env python3
"""Generate cat_1.png / cat_2.png -- the two-frame blocky pixel-art cat
used by overlay_litterbox.yaml's animimg widget (a blink cycle, not a
real animated GIF -- LVGL just alternates the two static images).

Re-run this (`pip install pillow && python3 gen_cat.py`) after editing
FRAME_OPEN/FRAME_BLINK below; don't hand-edit the PNGs pixel-by-pixel.
Requires Pillow. Output is RGBA with a real alpha channel (background
alpha 0) -- that's what ESPHome's `type: RGB565` +
`transparency: chroma_key` image encoder keys off, not a magic color.
"""

from pathlib import Path

from PIL import Image

BLOCK = 8  # scale factor: one grid cell -> BLOCK x BLOCK real pixels
GRID_W = 16
GRID_H = 16

PALETTE = {
    ".": (0, 0, 0, 0),  # transparent
    "K": (30, 30, 30, 255),  # outline / black
    "O": (224, 138, 60, 255),  # orange tabby body
    "D": (196, 110, 40, 255),  # darker orange (stripes/shade)
    "W": (245, 245, 245, 255),  # white muzzle/chest
    "P": (240, 140, 160, 255),  # pink nose/ears
    "E": (70, 200, 90, 255),  # green eyes (open)
}

FRAME_OPEN = [
    "................",
    "...KK......KK...",
    "..KOOK....KOOK..",
    "..KOPOK..KOPOK..",
    ".KOOOOKKKKOOOOK.",
    "KOOOOOOOOOOOOOOK",
    "KODOOOOOOOOOODOK",
    "KOOWWWOOOOWWWOOK",
    "KOOWEWOOOOWEWOOK",
    "KOOWWWOOOOWWWOOK",
    "KOOOOOOPPOOOOOOK",
    "KODOOOOOOOOOODOK",
    ".KWWOOOOOOOOWWK.",
    "..KWWOOOOOOWWK..",
    "...KKKKKKKKKK...",
    "................",
]

# Blink frame: eyes replaced by a flat closed-eye line.
FRAME_BLINK = [
    "................",
    "...KK......KK...",
    "..KOOK....KOOK..",
    "..KOPOK..KOPOK..",
    ".KOOOOKKKKOOOOK.",
    "KOOOOOOOOOOOOOOK",
    "KODOOOOOOOOOODOK",
    "KOOWWWOOOOWWWOOK",
    "KOOWKWOOOOWKWOOK",
    "KOOWWWOOOOWWWOOK",
    "KOOOOOOPPOOOOOOK",
    "KODOOOOOOOOOODOK",
    ".KWWOOOOOOOOWWK.",
    "..KWWOOOOOOWWK..",
    "...KKKKKKKKKK...",
    "................",
]


def render(frame: list[str], path: Path) -> None:
    img = Image.new("RGBA", (GRID_W * BLOCK, GRID_H * BLOCK), (0, 0, 0, 0))
    px = img.load()
    for row in range(GRID_H):
        for col in range(GRID_W):
            c = PALETTE[frame[row][col]]
            for by in range(BLOCK):
                for bx in range(BLOCK):
                    px[col * BLOCK + bx, row * BLOCK + by] = c
    img.save(path)


if __name__ == "__main__":
    here = Path(__file__).parent
    render(FRAME_OPEN, here / "cat_1.png")
    render(FRAME_BLINK, here / "cat_2.png")
    print("wrote cat_1.png, cat_2.png")
