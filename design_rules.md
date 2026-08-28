# FRAM M5Dial — Design and Build Specification

As of: 2026-08-21. Applies to all pages of the cockpit dashboard.
If a page deviates from this document, either the page is wrong or this
document is outdated — either way it must be corrected, not ignored.

---

## 1. Target device

| | |
|---|---|
| Device | M5Stack Dial (M5StampS3, ESP32-S3FN8, **no PSRAM**) |
| Display | GC9A01A, 240 × 240, round, via `mipi_spi` |
| Mounting | Dashboard / driver position |
| Controls | Rotary encoder, front button, capacitive touch (FT5x06) |
| Buzzer | GPIO3, via `rtttl:` (`rtttl_player`) |
| Flash | 8 MB (`flash_size: 8MB` under `esp32:`) |
| Rotation | `rotation: 0` |

Consequence of "round": anything beyond r = 120 px from the center
doesn't exist. The simulator shows a square and lies at the corners.

---

## 2. File structure

| File / folder | Contains |
|---|---|
| `.m5dial_fram.yaml` | everything shared by every M5 Dial in the FRAM (Location-specific: hardware header, palette grid, day/night) |
| `m5dial_fram_cockpit.yaml` | one specific dial (Device-specific: name, home page, which pages in which order) |
| `m5dial_pages/` | all pages, one file each, reusable across every dial in the project |
| `m5dial_pages/page_<name>.yaml` | one page, ready to `!include` as-is — no separate simulator variant, no merge step |
| `m5dial_pages/overlay_<name>.yaml` | an overlay (§15) — adds to LVGL's `top_layer`, not `pages:`; no page order, no `p<n>` slot |

One file per page, named `page_<name>.yaml`, `<name>` matching §10's
page names (`clock`, `gas`, `power_1`, `power_2`, `power_3`, `water`). Each file
directly contains its data sources (`sensor:` / `text_sensor:` on
`platform: homeassistant`), its bindings, and its widgets — this is
what actually runs on the device, not an intermediate form.

> No spaces in file names. `esphome config strom 2.yaml` passes two
> file names and fails twice. Multi-word file names use `_`, never `-`
> (`m5dial_fram_cockpit.yaml`, not `m5dial-fram-cockpit.yaml`) — that's
> a filename rule only, not a rule for `name:`/`friendly_name:` values.
> `name:` becomes a hostname and stays dash-separated, since hostnames
> don't allow underscores. `friendly_name:` has no such constraint — an
> underscore there is a cosmetic choice, not an error.
>
> A file with no `esphome.name:` of its own — shared by every dial,
> like `.m5dial_fram.yaml` and `.basics.yaml` — gets a leading dot.
> Without it the ESPHome dashboard still lists it as a flashable device
> even though it isn't one.

There's deliberately no maintained simulator build alongside this —
see §11.

---

## 3. Layout grid

Sits as `substitutions:` at the very top of **every** page file, with
identical values. When merging, this becomes a single block.

```yaml
substitutions:
  y_main:   "-20"
  y_line2:  "15"
  y_row:    "48"
  y_row2:   "78"
  y_footer: "-32"
  y_cap:    "-42"
  x_col:    "40"
```

`y_row2` is a second button row, for the rare page that needs four
buttons instead of two (`page_entrance`: step + lock, both two
momentary actions). Tighter than `y_row` because it's further from
center on a round display (§1) — check visually on the device.

`y_cap` and `x_col` are only needed by the two-value layout further
below. They still appear in every file, because otherwise the block
would no longer be identical and wouldn't collapse into one when
merging.

| Slot | Alignment | Content | Font |
|---|---|---|---|
| — | `TOP_MID`, y 46 | **free**, reserved for alarm icon | — |
| `y_cap` | `CENTER`, `x: ±${x_col}` | Column label, two-value layout only | `montserrat_12` |
| `y_main` | `CENTER` | Main value of the page | `montserrat_40` |
| `y_line2` | `CENTER` | Secondary line, context for the main value | `montserrat_16` |
| `y_row` | `CENTER` | Button row, 1 or 2 buttons | `montserrat_16` |
| `y_footer` | `BOTTOM_MID` | Status line, in the arc gap | `montserrat_12` |

No page title. The arc and the main value say where you are; a word
like "GRID" would use up the best space for the least information.
If a page doesn't need a slot, it stays empty — nothing moves up to
fill it. Otherwise the layout jumps while paging through.

### Where the values come from

LVGL positions a label around the center of its **line box**, not the
digits themselves. Line heights: `montserrat_12` 15 px, `_16` 20 px,
`_24` 29 px, `_40` 49 px; button 30 px.

| Slot | Box | Distance below |
|---|---|---|
| `y_cap` −42 | −49.5 … −34.5 | touches `y_main` |
| `y_main` −20 | m40: −44.5 … 4.5 · m24: −34.5 … −5.5 | 0.5 px box, ~15 px digits |
| `y_line2` 15 | 5 … 25 | 8 px |
| `y_row` 48 | 33 … 63 | 17.5 px |
| `y_footer` −32 | 80.5 … 95.5 | — |

The box gap between the main value and the secondary line computes to
zero and yet looks like the biggest one on the page: `montserrat_40`
sets the digits on the baseline, leaving roughly 10 px of empty box
below. **Calculate by line boxes, judge by digits.**

You can't go lower than this: at `y_row 54` the corners of the button
sit at radius 86.4, and the inner ring of a double-ring page sits at 90
(§8). And the footer starts at 80.5.

### Two equal-ranked values (Gas, Water)

Two tanks of the same kind have no main value and no secondary line —
neither is context for the other. They're therefore laid out as two
columns side by side, both on `x: ±${x_col}`:

| Row | y | Content | Font | Color |
|---|---|---|---|---|
| Label | `y_cap` | `FRESH` / `GREY`, `GAS A` / `GAS I` | `montserrat_12` | color of the associated ring |
| Value | `y_main` | `72%` | `montserrat_24` | main-value palette |
| Absolute | `y_line2` | `128 L`, `7.6 kg` | `montserrat_16` | `0xBDC1C6` |

`montserrat_40` doesn't work here: `100%` would be 100 px wide, and
each column only has about 80 px available.

The label row is the **only** mapping between column and ring —
concentric rings have no left and no right. It therefore carries the
color of its ring and is updated together with it in the drawing
script.

Where the two containers are distinguishable, the label names the
**content** (`FRESH` / `GREY`). Where they're identical, it names the
**ring**, not the mounting position: `GAS A` (outer) / `GAS I` (inner).
Two gas bottles sit one behind the other, so `LEFT` / `RIGHT` would
simply be wrong — and even where it happens to be correct, it doesn't
help, because the rings are concentric.

At most four characters in the value row and six in the label. At
`y_cap −42` the label has room up to x ±75 (inner radius 90); `GAS I`
comes to 57.5, `RECHTS` (RIGHT) to 62.5.

---

## 4. Geometry

| Quantity | Value |
|---|---|
| Display radius | 120 px |
| Arc | 224 × 224, `arc_width: 10` → ring from r = 102 to 112 |
| Arc angle | `start_angle: 135`, `end_angle: 45` → gap at the bottom |
| Usable inner radius | 102 px (118 px in the bottom gap) |

The gap at the bottom isn't a style choice — it's the space reserved
for `y_footer`.

Available text width at height y (distance from center):

| y | Width (r = 102) | Width in the gap (r = 118) |
|---|---|---|
| 40 | 187 px | — |
| 58 | 168 px | — |
| 65 | 157 px | — |
| 80 | — | 173 px |
| 90 | — | 152 px |

**Calculate the text width before every new layout**, don't estimate
it. The longest string that actually occurs counts, not the
placeholder: `PARK AUS` (PARK OFF) is wider than `---`, `ABSORPTION`
wider than `BULK`.

### Double ring

Two values of the same kind get two concentric rings, not two half
arcs. Both run over the full 135 → 45 arc; the half-arc approach would
need `mode: REVERSE` for the second arc so it fills in the same
direction, and it would halve the resolution of each value.

| Ring | Size | `arc_width` | Radius | Content |
|---|---|---|---|---|
| outer | 224 × 224 | 10 | 102 – 112 | the more important value |
| inner | 200 × 200 | 10 | 90 – 100 | the secondary value |

**Both rings the same thickness.** Different thickness reads as
importance and never matches the actual precedence.
2 px of black remain between the rings.

Usable inner radius on a double-ring page: **90 px**.

| y | Width (r = 90) |
|---|---|
| 40 | 161 px |
| 50 | 149 px |
| 58 | 138 px |
| 65 | 124 px |

The bottom gap doesn't change — the footer still has 152 px at y 90.

Where two values are equally ranked (two gas bottles), "outer" and
"inner" still exist because the geometry forces it. Then the outer
ring gets whichever value is currently in use.

---

## 5. Fonts

Built into LVGL, **no custom font file**:

```yaml
lvgl:
  default_font: montserrat_16
```

| Alias in text | Font | Use |
|---|---|---|
| large | `montserrat_40` | main value |
| medium | `montserrat_24` | value in the two-value layout |
| normal | `montserrat_16` | secondary line, buttons |
| small | `montserrat_12` | footer, column label |

Only even sizes from 8 to 48 are available.

> **Experience:** An attempt with a custom OTF (`bpp: 4`, trimmed glyph
> list) shifted the button labels vertically. The font file's metrics
> didn't explain it — apparently ESPHome writes a different line height
> when generating the bitmap font. If a custom font is ever needed
> after all: switch it **one at a time**, starting with the button
> font, and keep the glyph list generous (include lowercase letters
> with descenders even if they don't appear in the text).

---

## 6. Color palette

Background always black. Day/night differs only in backlight
brightness, never in the color scheme.

> **Exception: the clock page.** White face, black hands by day — the
> real SBB station clock's own look, and genuinely nicer than the dark
> theme everywhere else. Too bright for a dark cabin at night, though,
> so instead of just dimming it, it inverts: black face, white hands —
> the same look this page had before. The second hand stays red either
> way. This is the one deliberate, permanent departure from "background
> always black" / "day and night never differ in color scheme" above;
> every other page follows both rules without exception.

| Purpose | Value |
|---|---|
| Background | `0x000000` |
| Main value, good | `0xFFFFFF` |
| Secondary line | `0xBDC1C6` |
| Footer, unobtrusive | `0x707070` |
| **Invalid / no value** | `0x555555` |
| Good / charged | `0x2ECC71` |
| Warning | `0xF39C12` |
| Alarm / error | `0xE74C3C` |
| Neutral active (grid, water, gas) | `0x4A9EFF` |
| Secondary ring, unobtrusively active | `0x9AA0A6` |
| Arc background track | `0x1A1C1E` |
| Button, inactive (fill / border) | `0x202124` / `0x3C4043` |
| Button, active green | `0x1B5E3A` / `0x2ECC71` |
| Button, active blue | `0x14324F` / `0x4A9EFF` |
| Button, active orange | `0x4F3814` / `0xF39C12` |

Color is never the sole carrier of information — the state is always
also shown as text on the button.

`0x9AA0A6` is new and hasn't been judged on the device yet. It's meant
for a ring whose fill level nobody normally cares about (grey water,
second gas bottle). `0xBDC1C6` would be brighter and would look, next
to the blue outer ring, like a value you're supposed to watch;
`0x707070` all but disappears at low fill levels. See §13.

### Thresholds

| Quantity | Warning | Alarm |
|---|---|---|
| Battery SOC | < 40 % | < 20 % |
| Starter battery | < 12.4 V | < 12.0 V |
| Grid load | ≥ 80 % | ≥ 95 % |
| Fresh water | < 25 % | < 10 % |
| Grey water | ≥ 80 % | ≥ 95 % |
| Gas, per bottle | < 25 % | < 10 % |

The thresholds always color **both**: the ring and the value, plus the
column label that carries the ring color.

### Precedence in the status line

The footer shows exactly one message and is empty in normal operation.
It's allowed to take on warning and alarm colors for that; that's the
only exception to "footer stays unobtrusive".

**Two different containers: rank first, then damage before
inconvenience.** On the water page that means `ABWASSER VOLL` (GREY
TANK FULL) before `FRISCHWASSER LEER` (FRESH WATER EMPTY) — an
overflowing grey tank is damage to the vehicle, an empty fresh tank is
not. Both conditions usually occur at the same time, so the tie needs a
deliberate rule. The suppressed value is shown as a number above
regardless.

**Two interchangeable containers: the combined supply counts, not the
individual value.** Two gas bottles are one supply with two chambers;
an empty bottle isn't an alarm as long as the other one is still
carrying. On the gas page, therefore:

| Condition | Text | Color |
|---|---|---|
| both < 10 % | `GAS LEER` (GAS EMPTY) | red |
| both < 25 % | `GAS KNAPP` (GAS LOW) | orange |
| one < 10 % | `GAS A LEER` / `GAS I LEER` (GAS A/I EMPTY) | grey |

The grey case assumes an automatic changeover exists (Truma Duo or
similar) — then it's a heads-up that a bottle is due for a refill, not
a call to action. Without automatic changeover it belongs on orange,
because then someone has to go outside.

---

## 7. Invalid values

A dashboard that keeps showing the last value when the connection is
lost is more dangerous than one that shows nothing. Every label
therefore checks for itself and falls back to `---` in `0x555555`.

```yaml
text: !lambda |-
  #ifdef USE_API
  if (!api_is_connected()) return std::string("---");
  #endif
  if (!id(s_soc).has_state()) return std::string("---");
  return str_sprintf("%.0f%%", x);
```

The `#ifdef USE_API` guard is the trick that makes block C portable
unchanged: in the simulator there's no `api:` block, so the check is
skipped and you see real values; on the device it kicks in
automatically. Without the guard the simulator would permanently show
`---`.

The placeholder keeps the unit: `START ---V` and `---%`, not `---`.
Otherwise the line width jumps on the first valid value.

This also applies to **buttons**: without a connection, `PARK ---`, not
`PARK AUS` (PARK OFF). "Off" is a statement about the vehicle's state
that you can't back up without a connection.

The initial text stored in the widget is likewise in `0x555555` —
otherwise the placeholder looks like a valid value before the first
sensor reading arrives.

The footer is exempt from the `---` rule: it's normally empty, and a
`---` there wouldn't be a missing value but a new state. Instead it
writes `KEINE VERBINDUNG` (NO CONNECTION) or `KEIN WERT` (NO VALUE) in
`0x555555`.

---

## 8. Widget conventions

### Button

| | one button | two buttons |
|---|---|---|
| Width | 104 px | 76 px, `x: ±40` |
| Height | 30 px | 30 px |
| Radius | 15 | 15 |

The button is rectangular, the display is round: the **corners** count,
not the center. At `y_row 48` the lower corner of a 104 px button sits
at radius 81.7 — still clean on a double-ring page (inner ring at 90).
From `y_row 56` on, it clips.

Label as a **child label** with `align: CENTER`:

```yaml
- button:
    id: btn_parkmode
    align: CENTER
    y: ${y_row}
    width: 104
    height: 30
    radius: 15
    bg_color: 0x202124
    border_width: 1
    border_color: 0x3C4043
    widgets:
      - label:
          id: lbl_parkmode
          align: CENTER
          text: "PARK ---"
          text_font: montserrat_16
          text_color: 0x555555
    on_click:
      - ...
```

> Don't use the button's own `text:` property. It's valid and gets set
> via `lvgl.button.update`, but looked worse in testing than the child
> label. Likewise leave out `pad_all: 0`.

With two buttons, the label must fit in three to four characters
(`ON` / `CHG` / `INV` / `OFF`, `10 A`). If that's not enough, the
second value doesn't belong in this row.

The button's fill and border are set via `lvgl.widget.update`
(`bg_color`, `border_color`), the label via `lvgl.label.update`.

### Arc

```yaml
- arc:
    id: arc_xxx
    align: CENTER
    width: 224
    height: 224
    start_angle: 135
    end_angle: 45
    min_value: 0
    max_value: 100
    adjustable: false
    arc_width: 10
    arc_color: 0x1A1C1E
    indicator:
      arc_width: 10
      arc_color: 0x2ECC71
    knob:
      bg_opa: TRANSP
```

The second ring of a double-ring page is the same block with
`width: 200` / `height: 200`; everything else stays the same, in
particular `arc_width: 10` and the angles. Geometry: see §4.

The arc always shows **0–100 %**, never a physical quantity. If the
quantity has no natural upper bound, it's converted to a percentage of
a sensible reference value (example, grid: input current as a
percentage of the configured current limit). A fixed absolute scale
means the arc is almost empty or almost full most of the time.

Value and indicator color belong in **one** `lvgl.arc.update` call, not
two in sequence:

```yaml
- lvgl.arc.update:
    id: arc_soc
    value: !lambda "return x;"
    indicator:
      arc_color: !lambda "return lv_color_hex(0xE74C3C);"
```

### Background

`disp_bg_color:` is deprecated, and a `bg_color:` directly under
`lvgl:` only covers the part a page leaves free. Instead:

```yaml
lvgl:
  default_font: montserrat_16
  bottom_layer:
    bg_color: 0x000000
    bg_opa: COVER
```

---

## 9. Bindings

**One value, one display** → `on_value` directly on the sensor.

**Several interdependent values** → one drawing script per page that
redraws the whole page; each sensor only calls `script.execute`:

```yaml
script:
  - id: draw_grid
    mode: restart
    then:
      - lvgl.arc.update: ...
      - lvgl.label.update: ...
```

Reason: otherwise, after one value changes, the line that depends on
both values would sit wrong until the next update of the other sensor.
The script reads via `id(sensor).state`, not via `x`.

The drawing script additionally belongs in `esphome: on_boot:` with
`priority: -100`. Otherwise the line sits on the placeholder until the
first sensor value arrives, which on the device can take minutes.

Vehicle-fixed constants (tank sizes, bottle weights) live as a literal
in the script, with a comment. Not in `substitutions:` — those must
stay identical across all pages — and not as `globals:`, because no
state is held on the dial. Currently: fresh 180 L, grey 90 L, gas
bottle 10.5 kg net.

---

## 10. Naming scheme

The short page name is the yaml file's own name (`m5dial_pages/<name>.yaml`):
`clock`, `gas`, `power_1`, `power_2`, `power_3`, `water`. All page-prefixed IDs use it,
e.g. `s_power_1_soc`, `page_power_2`, `draw_water`.

| Prefix | For |
|---|---|
| `page_` | page (`page_power_1`, `page_gas`) |
| `arc_` | arc |
| `lbl_` | label |
| `btn_` | button |
| `s_` | sensor / text sensor (data source) |
| `draw_` | a page's drawing script |

For two equal-ranked values, a suffix distinguishes the columns, using
the same abbreviation as in the label:
`lbl_water_pct_f` / `_g`, `lbl_gas_pct_a` / `_i`. This holds all the
way down to the sensor (`s_gas_a`, `s_gas_i`) — which bottle is
physically connected to the outer ring is then decided solely by the
`entity_id`.

The page IDs and their **order** are the navigation — the encoder
addresses via the index. Only change the order deliberately.

---

## 11. Simulation

There's no maintained simulator build. Reflashing the device is fast
enough to be the normal way to check a change — a separate simulator
variant per page just gave the sim and the device copies of the same
logic to drift apart by hand, which is exactly what caused most of the
bugs this document's addenda are about.

Simulation is still worth doing **occasionally, by hand**, when
changing something that's awkward to judge by reflashing repeatedly
(a new layout, a new status-line rule, a color threshold). To do that:
temporarily swap that one page's `platform: homeassistant` sensors for
`platform: template` ones that sweep values, on a throwaway local copy
— don't commit a sim variant back into `m5dial_pages/`. Worth keeping
in mind while doing that:

* Values **sweep the whole range**, so all color thresholds become
  visible without waiting (SOC ramps in steps of 4 from 100 to 0, the
  MP state cycles including `fault`).
* Two values on one page run with **different** `update_interval`s,
  otherwise the same combinations always occur and you never see the
  status-line precedence. This also applies to values that only appear
  together in one row (voltage and current): with the same interval
  and the same list length, the pair repeats.
* No `api:` block — otherwise the invalidity check (§7) kicks in and
  every value shows `---`.

On the device, the dial is always only a display and a set of buttons.
The source of truth lives in Home Assistant and Node-RED respectively;
no state is held locally.

---

## 12. Structure

The three-layer split in §2 exists for modularity and reuse: FRAM
(motorhome) is one location that could have more than one M5 Dial, so
whatever is shared by all of them — the hardware header, the palette,
the grid, day/night — belongs in `.m5dial_fram.yaml`, one device (this
dial specifically: its name, its home page, its page order) belongs in
`m5dial_fram_cockpit.yaml`, and pages belong in `m5dial_pages/`,
reusable by any dial in the project, not just this one.

---

## 13. Before flashing

1. Adding or reordering a page: update the `packages:` list in
   `m5dial_fram_cockpit.yaml` — that order **is** the page order (§10).
2. Check that no ID occurs twice and no display points to a deleted
   ID — that's the most common source of error, and ESPHome catches
   it as a hard error rather than a silent runtime bug.
3. Run `esphome config` against `m5dial_fram_cockpit.yaml` **before**
   flashing.

---

## 14. Open items

* **Color of the secondary ring.** `0x9AA0A6` is set, but only judged
  in the simulator. Decide on the device whether the ring next to it
  is too loud or too quiet.
* **`GAS A` / `GAS I`.** The label names the ring and assumes that
  "outer/inner" is understood as referring to the rings and not the gas
  locker. Check on the device whether that holds up without an
  explanation.
* **Legibility of `montserrat_24`** in the two-value layout, from the
  driver's position. If too small: drop the liter line and go to 28.
* **Both alarms at the same time.** The status line only shows the
  higher one. Whether that's enough, or whether a combined message is
  needed, will only show up in operation.
* **Confirmation for dangerous buttons.** `MP OFF` takes away shore
  power, charging, and 230 V; `RETRACT` on the leveling page retracts
  the jacks. Both should require a long press or a confirmation prompt,
  not just a second click while paging through. Once that UX exists,
  have it call `beep_confirm` (`.m5dial_fram.yaml`) -- the buzzer's
  already wired, this item is only the missing long-press/confirm
  logic itself.
* **Alert tone for the overlays.** Pre-flight-check and cat-litter-box
  are visual-only right now. A tone on the pre-flight overlay is worth
  adding once it exists; deliberately NOT on the cat-litter one --
  that one would fire far too often to stay a "pay attention" signal.
* **~~Level 2 with two buttons.~~** Built: `g_edit_target`
  (`.m5dial_fram.yaml`) lets a page arm one of its values for the
  encoder to adjust instead of paging, tap to switch which one. Only
  `page_fans` uses it so far (2 targets) — the dispatch in
  `encoder_adjust_up`/`_down` is hand-written per target, so a third
  page adopting this needs a branch added there too.
* **~~Special characters.~~** Turned out to be a real bug, not a
  someday concern: every Ä/Ö/Ü/ä/ö/ü/ß on the device showed as a tofu
  box — LVGL's built-in `montserrat_NN` fonts are ASCII-only, no
  Latin-1, and ESPHome can't add glyphs to an already-compiled font.
  Fixed by switching to custom-rasterized fonts (`.m5dial_fram.yaml`'s
  `font:` block, `font_12`/`_16`/`_24`/`_40`) with an explicit glyph
  list covering what's actually used, umlauts included. Not yet
  confirmed on the device — next flash should show it either fixed or
  not. The middle dot `·` is still untested and still avoided; add it
  to the glyph list first if it's ever needed.
* **Visual height of the main value.** `72%` and `540 W` sit on the
  same `y_main` but appear to be at different heights, because the
  percent sign reaches further up. Only decide whether this is a
  problem once actually paging through on the real device.

---

## 15. Page catalog

The full planned roster, in navigation order (§10 — the encoder
addresses pages by this index, so the order is deliberate, not
alphabetical). "Implemented" means a `page_<id>.yaml` exists in
`m5dial_pages/` and is wired into `m5dial_fram_cockpit.yaml`'s
`packages:`. "Draft" additionally means it's wired in, but its
entity_ids are placeholders (`PLACEHOLDER_*` or otherwise unverified)
that don't point at anything real yet — it'll compile and show `---`
everywhere rather than break the build, but check each one's
entity_ids (and, for `lights_outside`/`ipixel`, the whole design —
there was no spec to build against beyond
one line each) before relying on it.

| # | id | Content | Status |
|---|---|---|---|
| 0 | `clock` | Clock + outdoor temperature and date/weekday | implemented |
| 1 | `power_1` | Battery: SOC, park mode, starter voltage | implemented |
| 2 | `power_2` | Grid power: input power (arc, read-only), PowerAssist current limit (arc, encoder-adjustable) | implemented |
| 3 | `power_3` | Grid power, WR side: inverter load (arc, computed against the installed model's nominal rating), MultiPlus mode | implemented |
| 4 | `gas` | Two gas bottles (double ring, §4) | implemented |
| 5 | `water` | Fresh / grey water (double ring, §4) | implemented |
| 6 | `levelling` | Spirit level — sensor is **external** hardware, not on the dial | implemented |
| 7 | `climate` | Truma Combi 4 (gas only) room-heating side + fan mode; AC not installed yet | draft |
| 8 | `boiler` | Truma Combi 4 water-heating side: mode, actual temperature | draft |
| 9 | `fans` | Fan board (real) + Sprinter HVAC fan (**placeholder** — that PCB doesn't exist yet) | implemented |
| 10 | `lights_outside` | Entrance light, awning light (dimmable; dial only does on/off, no brightness) | draft |
| 11 | `entrance` | Step, door lock | implemented |
| 12 | `ipixel` | On/off and status only | draft |
| reserved | `lights_inside` | — | reserved, not designed yet |

Not pages — shown as an overlay on top of whatever page is current,
via LVGL's `top_layer` (`m5dial_pages/overlay_<name>.yaml`, §2), per
the `s_ignition` comment in `.m5dial_fram.yaml`:

| id | Content | Status |
|---|---|---|
| `OV1` | Pre-flight check overlay | not designed yet |
| `OV2` | Cat litter box overlay: red while the light is on, green for 5s when the fan starts, then off | implemented (`overlay_litterbox.yaml`) — placeholder text label, no cat icon (no icon font set up in this repo yet) |

Neither overlay is suppressed while driving yet — the `s_ignition`
mechanism for that is still just the comment, not wired to anything.
