# FRAM M5Dial — Design and Build Specification

As of: 2026-08-28. Applies to all pages of the cockpit dashboard.
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
| `m5dial_pages/assets/` | binary assets (`image:`/`animation:` source files) referenced by `file:` from a page or overlay; generated ones keep their generator script alongside (e.g. `gen_cat.py`) instead of being hand-edited |

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

### On/off-only pages

No arc, no numeric value — just one or two switches to read and
toggle (`page_lights_outside`, the reference example: two switches,
two columns). There'll be more of these; use the same shape rather
than reinventing it per page:

* Two switches, same rank → the two-column shape above, minus
  `y_line2` (nothing to put there): `y_cap` names the switch, a button
  at `y_row` both shows EIN/AUS and toggles it. One switch → the same
  button centered, no columns, but grown (`page_ipixel`: 140x36, not
  the usual 104x30) — a single focal control reads as too sparse at
  the usual size.
* `x_col` (40) is sized for narrow TEXT columns (percentages, short
  labels), not buttons — a button that wide at `x_col` leaves only a
  few px between the two, easy to misregister a tap on the wrong one.
  Use a literal, page-local x offset instead (same reasoning as a
  page-local y — §3's `y_cap`/`y_row` intro), wide enough for a
  comfortable ~20px gap at the button width in use, and check the
  outer corner still clears r=120 (`page_lights_outside`: x:±48 at
  76x30; a row further from center needs to shrink further, same
  logic as `y_row2` — `page_entrance`'s outer row is 64x24 at x:±42).
* A switch's on/off state reads via `binary_sensor:` on
  `platform: homeassistant` (works for `switch.*` and `input_boolean.*`
  alike — HA reports both as a plain on/off state), never `sensor:`.
* The button's `on_click` calls an `act_` script, which calls
  `switch.toggle` / `input_boolean.toggle` — never a service straight
  off the widget (§9's device-independence reason applies here too).
* If a page is driven by more than one switch as one group (two
  switches standing in for one control, `page_lights_outside`'s
  EINGANG) — decide once what "on" means for the pair (any-on, as
  there) and make toggling always drive both to the *same* target
  state. A button can't show or reach a mixed on/off state usefully.
* Give the page a double-click shortcut to its `act_` script(s) too
  (§14's "Double-click as a SET/toggle shortcut" — one switch calls it
  directly, two alternate via a `dc_<page>_cycle` script), unless a
  momentary/dangerous action makes that unsafe (`page_entrance`
  deliberately has none — see that file's header).

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

### on_load poll

"Can take minutes" above turned out to be the reported symptom, not
just a theoretical caveat: HA only pushes an entity's CURRENT value to
this device at API-connect time if HA already has one. An entity
that's still unknown/unavailable at that exact moment (a slow-polling
integration behind it, a device that hasn't reported yet) sends
nothing — and then only catches up whenever it next changes on its
own, which can be a long, unpredictable wait. A background timer would
poll pages nobody's looking at; instead, each page with entities worth
forcing gets a dedicated `poll_<page>` script, called from that page's
own `on_load:` trigger (an LVGL page property, fires when the page
becomes active — not the same thing as `esphome: on_boot:` above,
which only fires once at startup):

```yaml
script:
  - id: poll_grid
    then:
      - homeassistant.service:
          service: homeassistant.update_entity
          data:
            entity_id: sensor.some_entity
      # one homeassistant.service call per entity -- data:/data_template:
      # values must be plain strings, a YAML list under entity_id: is a
      # hard config error (§9's own `homeassistant.service` calls,
      # page_lights_outside.yaml hit this first)

lvgl:
  pages:
    - id: page_grid
      on_load:
        - script.execute: poll_grid
```

`homeassistant.service: homeassistant.update_entity` forces HA to
re-fetch/re-publish that entity now, which reaches this device the
same way any other state change would. Wired on every page that has a
real entity to poll — `page_clock`, `page_power_1`, `page_power_2`,
`page_power_3`, `page_gas`, `page_water`, `page_levelling`,
`page_climate`, `page_boiler`, `page_fans`, `page_lights_outside`,
`page_entrance`, `page_ipixel` — per user decision, deliberately not
split by guessing which integrations are already fast enough to skip:
the call is cheap, consistency won that tradeoff. Every page's entities
are polled now, including `page_fans`'s HVAC column
(`number.relay_2ch_hvac_hvac_fan_battery`, the real entity from the
separate relay-2ch-hvac ESPHome device, user-confirmed — see §14 for
this entity's own correction history). The only still-valid exception
would be an entity that plain doesn't exist yet — polling that would
just log a warning in HA for nothing.

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
| `poll_` | a page's on_load entity-refresh script (§9) |

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

* **`page_fans` entity_ids corrected (2nd round).** Both were wrong
  before: `number.fan_speed_control` → `number.fan_board_fan_speed`,
  `number.hvac_fan_battery` → `number.relay_2ch_hvac_hvac_fan_battery`
  — user-confirmed against the real HA registry, not guessed. The
  first of the two had already gone through one "verified" round that
  turned out not to be — no scheme here is guess-proof, re-check
  against the registry directly if either device's `name:` ever
  changes, don't re-derive from the slug convention.
* **~~Climate/boiler interlock.~~** New standard, built for
  `page_climate`/`page_boiler`, meant to generalize to any future AC
  control the same way: user report — turning HEIZUNG/BOILER on or off
  from the dial let SOLL (the target-temperature arm) keep being
  adjusted the whole time the Truma took (2-4s+) to confirm the real
  switch state, and the resulting writes just silently did nothing —
  "everything looked adjustable, none of it visibly did anything".
  SOLL's arm action already refused to ARM while not confirmed-on, but
  nothing stopped an ALREADY-armed SOLL from staying armed once the
  confirmed state flipped back to off. Now: (1) the heater/boiler
  switch's `on_state` auto-disarms (flushing any pending write first)
  the instant the CONFIRMED state goes to off while its target is
  armed; (2) the SOLL button/label render a third, visually distinct
  LOCKED state (dim border + dim label) whenever the device isn't
  confirmed on, instead of looking identical to the normal
  idle-available state; (3) the footer shows "HEIZUNG STARTET" /
  "BOILER STARTET" during the specific window where the optimistic
  guess already says on but confirmation hasn't arrived; (4) the
  double-click cycle only advances past its "arm" step once arming
  actually happened, instead of advancing regardless and flip-flopping
  the switch on/off if double-clicked again mid-confirmation. The
  general shape — a device's own confirmed on/off state gates its
  dependent target control, both in logic and visibly — is the pattern
  to copy for a future AC control, not a mode-cycle button (considered
  and dropped: the user's actual ask was this interlock, not a
  unified AUS/HEIZEN/KÜHLEN mode selector).
* **~~Two-switch pages: wider spacing, more legible status.~~** User
  report ("Sachen weiter auseinander, Status besser erkennbar") on
  `page_lights_outside`/`page_entrance` — confirmed in scope for just
  these two, not the still-reserved `page_lights_inside`. Both pages'
  button columns/rows moved further from center (still comfortably
  inside r=120 — see each file's own header for the new corner-radius
  math): `page_lights_outside` ±48 → ±60, `page_entrance`'s row 1
  ±48 → ±58 and row 2 ±42 → ±54. `page_lights_outside` additionally
  gained a second status channel: the column caption label (EINGANG/
  MARKISE) now carries the on-state color too (lit/dim), not just the
  button fill — the same idiom design.md §3 already uses for gas/
  water's column label carrying its ring's color, so this isn't a new
  invented convention. `page_entrance` has no per-row status to
  amplify (its buttons are momentary fire-once actions, not a stable
  on/off state), so only the spacing changed there.
* **~~FANBOARD's four per-channel readbacks, not yet surfaced.~~** Built,
  per user decision: not shown individually (four more numbers don't
  fit the double-ring shape) — instead `page_fans`'s `draw_fans` shows
  their Ø (average) on `y_line2` (otherwise unused on this page) plus
  a small red dot that lights up when any one channel is > 15
  percentage points off that average. The 15-point tolerance is a
  guess, not a measured one — revisit on the device, same status as
  the boiler tiers/levelling cm thresholds below.
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
  encoder to adjust instead of paging, tap to switch which one.
  `page_fans` (targets 1/2), `page_climate` (3), `page_boiler` (5) and
  `page_power_2` (6) use it now — the dispatch in
  `encoder_adjust_up`/`_down` is hand-written per target, so each page
  adopting this needs a branch added there too.
* **~~Double-click as a SET/toggle shortcut.~~** Built, then widened:
  double-click no longer ever falls back to the home page — that's
  long-press-only now, unconditionally, on every page. Instead,
  double-click runs the current page's own double-click action, if it
  has one (`LvPageType::is_showing()` picks the page, hand-written
  per-page dispatch in `.m5dial_fram.yaml`, same pattern as
  `encoder_adjust_up`/`_down`). A page with exactly one thing worth
  reaching calls it directly: `page_power_1` (`act_power_1_park`),
  `page_power_2` (`act_power_2_arm_assist`), `page_power_3`
  (`act_power_3_mode`), `page_water` (`act_water_pump`), `page_ipixel`
  (`act_ipixel_power`). A page with two exposes a dedicated
  `dc_<page>_cycle` script that alternates between them, one per
  click, instead of one fixed winner: `page_fans` (FANBOARD SET, then
  HVAC SET, then disarm — see below), `page_climate` and `page_boiler`
  (temp SET, then the HEIZ/BOILER on/off toggle — this is also how
  ordinary toggle buttons became double-click-reachable, not just
  encoder-SET ones), `page_lights_outside` (EINGANG, then MARKISE).
  `page_clock`/`page_gas`/`page_levelling` have nothing to act on;
  `page_entrance` deliberately has no double-click action at all (see
  that file's header — momentary step/lock actions aren't safe for a
  quick gesture while driving). `page_fans`'s cycle is state-driven
  (reads `g_edit_target` itself) rather than a separate position
  counter, unlike the other three two-action pages — a counter that
  just alternated between "call the FANBOARD arm script" / "call the
  HVAC arm script" turned out to never reach disarmed: each of those
  scripts only toggles ITS OWN target off if it was the one already
  armed, so bouncing between two different arm-style targets meant
  neither ever saw itself armed, and the encoder lock never released.
  `page_climate`/`page_boiler` don't have this bug (one arm-style
  target + one plain toggle, and the arm script's own built-in toggle
  naturally reaches "off" every other click) — but if a third
  multi-arm-target page ever needs a cycle, copy `page_fans`'s
  state-driven shape, not the position-counter one.
* **~~Encoder lag on adjustable values.~~** Built: every
  `number.set_value`/`climate.set_temperature` call used to fire on
  every single encoder detent, and the display waited for HA to
  confirm the new value before moving — turning fast felt laggy
  because the number was always one round trip (or, for the Truma
  targets, one Truma LIN round trip, ~2-4s) behind the knob. Now each
  adjustable target keeps a local `g_<page>_<name>_pending` value that
  the encoder edits directly and the display reads from while armed
  (zero perceived lag, no HA involved), and the actual write is
  debounced — restarted on every tick, only firing 400ms after the
  encoder goes quiet (`page_power_2`, `page_climate`, `page_boiler`,
  `page_fans`'s FANBOARD). Disarming (SET tapped again, or the
  double-click cycle moving past it) flushes the write immediately
  instead of waiting out the debounce. 400ms is a guess, not measured
  against real turning speed — adjust per-page if it still lags or
  fires mid-turn. Doesn't and can't touch the Truma's own ~2-4s
  hardware lag — that's physical, not a display problem.
* **SET → SOLL button label (`page_climate`/`page_boiler`).**
  Readability follow-up: a generic "SET" button sitting right next to
  "HEIZ EIN/AUS" / "BOILER EIN/AUS" didn't say which one was power and
  which was temperature. Renamed to SOLL, matching the SOLL line it
  arms — the on/off button's own label already says what it does,
  this just needed to say the same about the other one.
* **`page_boiler`'s three fixed temperature tiers, not a continuous
  range.** This Truma boiler only actually supports ECO (40°C), an
  unnamed middle level (60°C — ask before labelling it, don't guess),
  and BOOST (80°C) — confirmed by the user, not documented anywhere
  ESPHome-side. `act_boiler_temp_up`/`_down` step between exactly
  those three now instead of ±1°C across a guessed 30-70 range.
  `page_climate`'s room temp is unaffected — that side of the same
  Truma Combi 4 genuinely is continuous.
* **Real integration behind `climate`/`boiler`.** Both originally
  assumed a `truma_inetbox` external ESPHome component talking LIN
  directly — wrong; the real path is a MQTT-based `womolin_controller`
  integration (`switch.womolin_controller_mqtt_activate_room_heater` /
  `_water_heater`, `climate.womolin_controller_mqtt_truma_room` /
  `_water`). Current/target temperature and the on/off gate are wired
  to that now. Fan mode/level and a fault flag existed on the old
  assumption and were dropped rather than re-guessed — add them back
  once the real attribute/entity for either is confirmed on the
  `womolin_controller` climate entities.
* **PowerAssist setpoint vs. applied value (`page_power_2`).** The
  ASSIST button shows `number.multiplus_strombegrenzung`, the
  setpoint — there's no separate entity confirming the MultiPlus has
  actually settled on that limit over VE.Bus, so the display can lag
  the real applied value briefly after a change. Nothing to fix
  without a second entity for the applied value.
* **Corner cm thresholds (`page_levelling`).** `< 1.5cm` ok,
  `1.5-3cm` warning, `>= 3cm` alarm are a guess, same status the old
  degree thresholds had — not measured against a real leveling
  requirement. Values also round to whole cm for legibility; revisit
  if that's not enough precision in practice. Also now clamped to
  `>= 0` rather than shown signed — this reads as "how many cm to
  wedge under this corner", and a negative source reading just means
  "this one's fine", not "let air out" (there's no air suspension
  here to relate a minus sign to).
* **`page_levelling`'s four corner sensors all read 0 right now** —
  `sensor.mpu6050_womo_vl_cm`/`_vr_cm`/`_hl_cm`/`_hr_cm` exist as
  entity_ids but nothing upstream computes real values into them yet.
  Per user decision: build the degrees-to-cm conversion in HA (one
  template sensor per corner, using the vehicle's real track
  width/wheelbase) rather than in this page — this page was already
  written to only ever consume four finished entities (see its own
  header), so nothing here needs to change once those HA-side sensors
  exist.
* **Special characters — still reported broken on the device, audited,
  no further code bug found.** Every Ä/Ö/Ü/ä/ö/ü/ß showed as a tofu box
  under LVGL's built-in `montserrat_NN` fonts (ASCII-only, no Latin-1;
  ESPHome can't add glyphs to an already-compiled font) — fixed once
  already by switching to custom-rasterized fonts (`.m5dial_fram.yaml`'s
  `font:` block, `font_12`/`_16`/`_24`/`_40`) with an explicit glyph
  list. User report (2026-09-06): still seeing tofu boxes after that
  fix, with an explicit warning not to repeat the smart-ebl-display
  repo's OWN umlaut bug — there, the glyph list was a `|-` block
  scalar with the leading space meant to be its first character, and
  YAML's block-scalar indentation stripping silently ate exactly that
  character, so every plain space (not just umlauts) rendered as a
  tofu box too. Audited this repo's version specifically against that
  failure mode and it does NOT have it: the glyph string here is a
  quoted flow scalar (one line, in quotes), which has no such stripping
  rule, and its leading space is intact. Also checked and ruled out:
  every non-ASCII character actually used in any page's `text:`/lambda
  strings is in the glyph list (cross-checked programmatically), and
  no widget's `text_font:` was left pointing at a bare `montserrat_NN`
  (only page_clock's `date_font`/`temperature_font` still are, and
  neither renders German text). So the glyph declaration itself looks
  correct in the current source — the leading theory is that the
  device simply hadn't been reflashed since this fix landed. Still
  open: confirm on a fresh flash; if it's STILL broken after that,
  the bug is somewhere this audit didn't reach (worth checking next:
  whether `gfonts://Montserrat` without an explicit weight actually
  ships the accented glyphs it claims to, by trying a pinned weight
  like `gfonts://Montserrat@700` or a local TTF instead). The middle
  dot `·` is still untested and still avoided; add it to the glyph
  list first if it's ever needed — the same one-line-string rule
  applies to any future addition (Ø, added for `page_fans`'s channel
  average, already follows it).
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
| 2 | `power_2` | Grid power: input power (single arc + big value, read-only), PowerAssist current limit (value + SET button, encoder-adjustable) | implemented |
| 3 | `power_3` | Grid power, WR side: inverter load (arc, computed against the installed model's nominal rating), MultiPlus mode | implemented |
| 4 | `gas` | Two gas bottles (double ring, §4) | implemented |
| 5 | `water` | Fresh / grey water (double ring, §4) | implemented |
| 6 | `levelling` | Spirit level (bubble, MPU6050) + per-corner cm-to-add (VL/VR/HL/HR, from four already-computed sensors) | implemented |
| 7 | `climate` | Truma Combi 4 (gas only) room-heating side, via the `womolin_controller` MQTT integration's activate switch + climate entity; AC not installed yet; fan mode/fault dropped pending a confirmed entity | implemented |
| 8 | `boiler` | Truma Combi 4 water-heating side, same `womolin_controller` integration as `climate` | implemented |
| 9 | `fans` | Fan board (`number.fan_board_fan_speed`) + Sprinter HVAC fan (`number.relay_2ch_hvac_hvac_fan_battery`, real — driven by the separate relay-2ch-hvac ESPHome device; that board only actually moves the motor when parked, this page just sets the desired value) | implemented |
| 10 | `lights_outside` | Entrance light (two switches, driven together), awning light — both plain switches, not the `light` domain | implemented |
| 11 | `entrance` | Step, door lock — rows grouped by purpose: REIN+ZU (securing to drive) / RAUS+AUF (arriving), not by device; no double-click shortcut (safety) | implemented |
| 12 | `ipixel` | On/off (`input_boolean`) + per-side LED status (two switches) | implemented |
| reserved | `lights_inside` | — | reserved, not designed yet |

Not pages — shown as an overlay on top of whatever page is current,
via LVGL's `top_layer` (`m5dial_pages/overlay_<name>.yaml`, §2), per
the `s_ignition` comment in `.m5dial_fram.yaml`:

| id | Content | Status |
|---|---|---|
| `OV1` | Pre-flight check overlay: red while `binary_sensor.pre_flight_check` is off (failed) AND ignition is on/starting | implemented (`overlay_preflight.yaml`) — blocky pixel-art warning triangle (pulses amber/white, `gen_warning.py`), generic message text (not the actual failed-items list, see that file's header open item), dismissible early |
| `OV2` | Cat litter box overlay: red while the light is on, green for 5s when the fan starts, then off | implemented (`overlay_litterbox.yaml`) — blocky pixel-art cat (`m5dial_pages/assets/`, animimg 2-frame blink), dismissible early |
| `OV3` | iPixel-on overlay: red while either front LED switch is on | implemented (`overlay_ipixel.yaml`) — text only, dismissible early |

All overlays are dismissible early: double-clicking the physical front
button while one is showing acknowledges and hides it instead of
running whatever that double-click would otherwise do on the current
page — dismissing always wins first (`.m5dial_fram.yaml`'s
double-click handler checks each overlay's root widget before
deciding what else to do). A page adding a new overlay needs to: give
its root `obj:` widget an `<name>_ack` script (hide + set a page-local
`g_ov_<name>_ack` global, guarded so it's a no-op when that overlay
isn't the one currently showing — see any existing overlay for the
shape), reset that ack global to false once its own trigger condition
goes false again, and add a branch for it to the double-click
handler's hard-coded list — same "add a branch here" pattern as
`encoder_adjust_up`/`_down`.

`overlay_preflight` is gated on `s_ignition` (state 4/5 = on/starting)
— the first real use of the "suppresses the overlays" idea that
comment used to only anticipate. `overlay_litterbox`/`overlay_ipixel`
still aren't suppressed while driving.
