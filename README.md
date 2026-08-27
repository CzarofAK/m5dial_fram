# m5dial_fram
This repo holds my yaml files for the m5dials in my motorhome (FRAM).

See [`design_rules.md`](design_rules.md) for the full design and build
specification — layout grid, geometry, colors, naming scheme, and the
checklist for merging a page into a device file.

## Prerequisite: `.basics.yaml`

`.m5dial_fram.yaml` (the header shared by every M5 Dial in the FRAM)
assumes a `.basics.yaml` already sits next to the device file in the
ESPHome directory — it is **not** included from this repo, since it's
shared by every ESPHome device in the install, not just the M5 Dials.

Both are dot-prefixed on purpose: neither has an `esphome.name:` of
its own, but the ESPHome dashboard still lists an undotted file here
as a flashable device — the leading dot keeps it out of that listing.

It needs to provide: `wifi`, `ota`, `api`, `web_server`, `logger`, the
`homeassistant_time` time source, and a `restart_button`.

[`basics.example.yaml`](basics.example.yaml) is a template for it —
copy it to `/config/esphome/.basics.yaml` and fill in your own secrets.
It expects these keys in `secrets.yaml`: `wifi_ssid`, `wifi_password`,
`password` (OTA), `api_encryption_key`, `ap_password`.
