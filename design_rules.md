# FRAM M5Dial — Design- und Bauvorschrift

Stand: 21.08.2026. Gilt für alle Seiten des Cockpit-Dashboards.
Wenn eine Seite von diesem Dokument abweicht, ist entweder die Seite falsch
oder dieses Dokument veraltet — beides gehört korrigiert, nicht ignoriert.

> **Nachtrag 21.08.2026 (1), aus dem Bau von Seite 4 (Wasser).** Neu bzw.
> geändert: §3 Zwei-Wert-Layout und zwei zusätzliche Substitutions, §4
> Doppelring und der dadurch kleinere Innenradius, §5 `montserrat_24`,
> §6 Wasser-Schwellen, Rangfolge der Statuszeile, Farbe des nachrangigen
> Rings, §8 zweiter Ring.

> **Nachtrag 21.08.2026 (2), aus dem Bau von Seite 3 (Gas) und der
> Überarbeitung von Seite 1.** Neu bzw. geändert: §3 **alle
> Rasterwerte** — der Stapel lag zu hoch, unten stand das Loch; §3
> Beschriftung der Spalten benennt den Ring, nicht die Einbaulage; §6
> Gas-Schwellen und eine Rangfolge für zwei gleichwertige Vorräte; §8
> Eckenradius des Tasters auf Doppelring-Seiten.
>
> **Die Seiten 2 und 4 stehen noch auf dem alten Raster.** Sie werden
> beim ersten Zusammenführen nachgezogen, wo der Substitutions-Block
> ohnehin nur noch einmal vorkommt. Bis dahin sitzen sie im Simulator
> ein paar Pixel höher als Seite 1 und 3.

---

## 1. Zielgerät

| | |
|---|---|
| Gerät | M5Stack Dial (M5StampS3, ESP32-S3FN8, **kein PSRAM**) |
| Display | GC9A01A, 240 × 240, rund, über `mipi_spi` |
| Einbau | Armaturenbrett / Fahrerposition |
| Bedienung | Drehencoder, Fronttaste, kapazitiver Touch (FT5x06) |
| Flash | 8 MB (`flash_size: 8MB` unter `esp32:`) |
| Rotation | `rotation: 180` |

Konsequenz aus „rund": alles jenseits von r = 120 px vom Mittelpunkt
existiert nicht. Der Simulator zeigt ein Quadrat und lügt an den Ecken.

---

## 2. Dateistruktur

Eine Datei pro Seite, benannt `sim_NN_kurzname.yaml`. Jede Datei ist für
sich im SDL2-Simulator lauffähig:

```
esphome run sim_02_netz.yaml
```

> Keine Leerzeichen in Dateinamen. `esphome config strom 2.yaml` übergibt
> zwei Dateinamen und schlägt zweimal fehl.

Jede Datei ist in vier Blöcke geteilt, in dieser Reihenfolge:

| Block | Inhalt | beim Zusammenführen |
|---|---|---|
| **A** Gerüst | `esphome:`, `host:`, `display: sdl`, `touchscreen: sdl`, Sim-Globals | **entfällt**, ersetzt durch die Hardware-Datei |
| **B** Datenquellen | `sensor:` / `text_sensor:` mit `platform: template` | **getauscht** gegen `platform: homeassistant` |
| **C** Bindings | `on_value`-Trigger bzw. Zeichenskripte | **1 : 1** übernommen |
| **D** Widgets | `lvgl: pages: - id: page_xxx` | **1 : 1** übernommen, als eine Seite |

Der Sinn der Trennung: Blöcke C und D sind der eigentliche Wert und dürfen
beim Übertragen nicht angefasst werden müssen. Alles, was sich zwischen
Simulator und Gerät unterscheidet, steckt in A und B.

---

## 3. Layout-Raster

Steht als `substitutions:` ganz oben in **jeder** Seitendatei, mit
identischen Werten. Beim Zusammenführen wird daraus ein einziger Block.

```yaml
substitutions:
  y_main:   "-20"
  y_line2:  "15"
  y_row:    "48"
  y_footer: "-32"
  y_cap:    "-42"
  x_col:    "40"
```

`y_cap` und `x_col` braucht nur das Zwei-Wert-Layout weiter unten. Sie
stehen trotzdem in jeder Datei, weil der Block sonst nicht mehr identisch
ist und beim Zusammenführen nicht zusammenfällt.

| Slot | Ausrichtung | Inhalt | Schrift |
|---|---|---|---|
| — | `TOP_MID`, y 46 | **frei**, Reserve für Alarm-Icon | — |
| `y_cap` | `CENTER`, `x: ±${x_col}` | Spaltenbeschriftung, nur Zwei-Wert-Layout | `montserrat_12` |
| `y_main` | `CENTER` | Hauptwert der Seite | `montserrat_40` |
| `y_line2` | `CENTER` | Nebenzeile, Kontext zum Hauptwert | `montserrat_16` |
| `y_row` | `CENTER` | Tasterreihe, 1 oder 2 Taster | `montserrat_16` |
| `y_footer` | `BOTTOM_MID` | Statuszeile, in der Bogenlücke | `montserrat_12` |

Kein Seitentitel. Der Bogen und der Hauptwert sagen, wo man ist; ein Wort
wie „NETZ" verbraucht den besten Platz für die geringste Information.
Wenn eine Seite einen Slot nicht braucht, bleibt er leer — nicht
nachrücken. Sonst springt das Bild beim Durchdrehen.

### Woher die Werte kommen

LVGL positioniert ein Label über die Mitte seines **Zeilenkastens**, nicht
über die Ziffern. Zeilenhöhen: `montserrat_12` 15 px, `_16` 20 px, `_24`
29 px, `_40` 49 px; Taster 30 px.

| Slot | Kasten | Abstand nach unten |
|---|---|---|
| `y_cap` −42 | −49.5 … −34.5 | berührt `y_main` |
| `y_main` −20 | m40: −44.5 … 4.5 · m24: −34.5 … −5.5 | 0.5 px Kasten, ~15 px Ziffern |
| `y_line2` 15 | 5 … 25 | 8 px |
| `y_row` 48 | 33 … 63 | 17.5 px |
| `y_footer` −32 | 80.5 … 95.5 | — |

Der Kastenabstand zwischen Hauptwert und Nebenzeile ist rechnerisch null
und optisch trotzdem der grösste auf der Seite: `montserrat_40` setzt die
Ziffern auf die Grundlinie, unter der etwa 10 px Kasten leer bleiben.
**Nach Zeilenkästen rechnen, nach Ziffern beurteilen.**

Weiter nach unten geht nicht: bei `y_row 54` liegen die Ecken des Tasters
auf Radius 86.4, der Innenring einer Doppelring-Seite sitzt bei 90 (§8).
Und die Fusszeile beginnt bei 80.5.

### Zwei gleichrangige Werte (Gas, Wasser)

Zwei Tanks derselben Art haben keinen Hauptwert und keine Nebenzeile —
der eine ist nicht Kontext zum anderen. Sie stehen deshalb als zwei
Spalten nebeneinander, beide auf `x: ±${x_col}`:

| Zeile | y | Inhalt | Schrift | Farbe |
|---|---|---|---|---|
| Beschriftung | `y_cap` | `FRISCH` / `GRAU`, `GAS A` / `GAS I` | `montserrat_12` | Farbe des zugehörigen Rings |
| Wert | `y_main` | `72%` | `montserrat_24` | Palette Hauptwert |
| Absolut | `y_line2` | `128 L`, `7.6 kg` | `montserrat_16` | `0xBDC1C6` |

`montserrat_40` geht hier nicht: `100%` wäre 100 px breit, pro Spalte
stehen gut 80 px zur Verfügung.

Die Beschriftungszeile ist die **einzige** Zuordnung zwischen Spalte und
Ring — konzentrische Ringe haben kein Links und kein Rechts. Sie trägt
deshalb die Farbe ihres Rings und wird im Zeichenskript mitgeführt.

Wo die beiden Behälter unterscheidbar sind, benennt die Beschriftung den
**Inhalt** (`FRISCH` / `GRAU`). Wo sie gleich sind, benennt sie den
**Ring**, nicht die Einbaulage: `GAS A` (aussen) / `GAS I` (innen). Zwei
Gasflaschen stehen hintereinander, `LINKS` / `RECHTS` wäre schlicht
falsch — und selbst wo es stimmt, hilft es nicht, weil die Ringe
konzentrisch sind.

Höchstens vier Zeichen in der Wertzeile und sechs in der Beschriftung.
Bei `y_cap −42` reicht die Beschriftung bis x ±75 (Innenradius 90);
`GAS I` kommt auf 57.5, `RECHTS` auf 62.5.

---

## 4. Geometrie

| Grösse | Wert |
|---|---|
| Displayradius | 120 px |
| Arc | 224 × 224, `arc_width: 10` → Ring von r = 102 bis 112 |
| Arc-Winkel | `start_angle: 135`, `end_angle: 45` → Lücke unten |
| Nutzbarer Innenradius | 102 px (in der unteren Lücke 118 px) |

Die Lücke unten ist kein Stilelement, sondern der Platz für `y_footer`.

Verfügbare Textbreite auf Höhe y (Abstand vom Mittelpunkt):

| y | Breite (r = 102) | Breite in der Lücke (r = 118) |
|---|---|---|
| 40 | 187 px | — |
| 58 | 168 px | — |
| 65 | 157 px | — |
| 80 | — | 173 px |
| 90 | — | 152 px |

**Vor jedem neuen Layout die Textbreite nachrechnen**, nicht schätzen.
Der längste real vorkommende String zählt, nicht der Platzhalter:
`PARK AUS` ist breiter als `---`, `ABSORPTION` breiter als `BULK`.

### Doppelring

Zwei Werte derselben Art bekommen zwei konzentrische Ringe, nicht zwei
Halbarcs. Beide laufen über den vollen Bogen 135 → 45; die Halbarc-Lösung
brauchte für den zweiten Bogen `mode: REVERSE`, damit er in dieselbe
Richtung füllt, und halbierte die Auflösung jedes Werts.

| Ring | Grösse | `arc_width` | Radius | Inhalt |
|---|---|---|---|---|
| aussen | 224 × 224 | 10 | 102 – 112 | der wichtigere Wert |
| innen | 200 × 200 | 10 | 90 – 100 | der nachrangige Wert |

**Beide Ringe gleich dick.** Unterschiedliche Dicke liest sich als
Wichtigkeit und stimmt nie mit der tatsächlichen Rangfolge überein.
Zwischen den Ringen bleiben 2 px Schwarz.

Nutzbarer Innenradius auf einer Doppelring-Seite: **90 px**.

| y | Breite (r = 90) |
|---|---|
| 40 | 161 px |
| 50 | 149 px |
| 58 | 138 px |
| 65 | 124 px |

Die Lücke unten ändert sich nicht — die Fusszeile hat weiterhin 152 px
bei y 90.

Wo zwei Werte gleichrangig sind (zwei Gasflaschen), gibt es „aussen" und
„innen" trotzdem, weil die Geometrie es erzwingt. Dann bekommt der Ring
aussen den Wert, der gerade in Betrieb ist.

---

## 5. Schriften

LVGL-intern, **keine eigene Font-Datei**:

```yaml
lvgl:
  default_font: montserrat_16
```

| Alias im Text | Schrift | Verwendung |
|---|---|---|
| gross | `montserrat_40` | Hauptwert |
| mittel | `montserrat_24` | Wert im Zwei-Wert-Layout |
| normal | `montserrat_16` | Nebenzeile, Taster |
| klein | `montserrat_12` | Fusszeile, Spaltenbeschriftung |

Verfügbar sind gerade Grössen von 8 bis 48.

> **Erfahrung:** Ein Versuch mit eigener OTF (`bpp: 4`, beschnittene
> Glyphenliste) hat die Beschriftung in den Tastern vertikal verschoben.
> Die Metrik der Schriftdatei erklärte das nicht — offenbar trägt ESPHome
> beim Erzeugen der Bitmap-Schrift eine andere Zeilenhöhe ein. Falls doch
> einmal eine eigene Schrift nötig wird: **einzeln** umstellen, zuerst die
> Tasterschrift, und die Glyphenliste grosszügig halten (Kleinbuchstaben
> mit Unterlängen einschliessen, auch wenn sie im Text nicht vorkommen).

---

## 6. Farbpalette

Hintergrund immer schwarz. Tag/Nacht unterscheidet sich nur in
Backlight-Helligkeit, nie im Farbschema.

| Zweck | Wert |
|---|---|
| Hintergrund | `0x000000` |
| Hauptwert, gut | `0xFFFFFF` |
| Nebenzeile | `0xBDC1C6` |
| Fusszeile, unauffällig | `0x707070` |
| **Ungültig / kein Wert** | `0x555555` |
| Gut / geladen | `0x2ECC71` |
| Warnung | `0xF39C12` |
| Alarm / Fehler | `0xE74C3C` |
| Neutral aktiv (Netz, Wasser, Gas) | `0x4A9EFF` |
| Nachrangiger Ring, unauffällig aktiv | `0x9AA0A6` |
| Bogen-Hintergrundbahn | `0x1A1C1E` |
| Taster, inaktiv (Fläche / Rand) | `0x202124` / `0x3C4043` |
| Taster, aktiv grün | `0x1B5E3A` / `0x2ECC71` |
| Taster, aktiv blau | `0x14324F` / `0x4A9EFF` |
| Taster, aktiv orange | `0x4F3814` / `0xF39C12` |

Farbe ist nie der einzige Träger einer Information — der Zustand steht
zusätzlich als Text auf dem Taster.

`0x9AA0A6` ist neu und noch nicht am Gerät beurteilt. Er soll einen Ring
zeigen, dessen Füllstand im Normalfall niemanden interessiert (Grauwasser,
zweite Gasflasche). `0xBDC1C6` wäre heller und würde neben dem blauen
Aussenring nach einem Wert aussehen, den man ansehen soll; `0x707070`
verschwindet bei kleinem Füllstand fast. Siehe §13.

### Schwellen

| Grösse | Warnung | Alarm |
|---|---|---|
| Batterie-SOC | < 40 % | < 20 % |
| Starterbatterie | < 12.4 V | < 12.0 V |
| Netzauslastung | ≥ 80 % | ≥ 95 % |
| Frischwasser | < 25 % | < 10 % |
| Grauwasser | ≥ 80 % | ≥ 95 % |
| Gas, je Flasche | < 25 % | < 10 % |

Die Schwellen färben immer **beides**: den Ring und den Wert, plus die
Spaltenbeschriftung, die die Ringfarbe trägt.

### Rangfolge in der Statuszeile

Die Fusszeile zeigt genau eine Meldung und ist im Normalbetrieb leer. Sie
darf dafür Warn- und Alarmfarbe annehmen; das ist die einzige Ausnahme
von „Fusszeile unauffällig".

**Zwei verschiedene Behälter: erst Rang, dann Schaden vor Unbequemlichkeit.**
Auf der Wasserseite heisst das `ABWASSER VOLL` vor `FRISCHWASSER LEER` —
ein überlaufender Grautank ist Schaden im Fahrzeug, ein leerer Frischtank
nicht. Beide Zustände treten meist gleichzeitig ein, der Gleichstand
braucht also eine bewusste Regel. Der unterdrückte Wert steht ohnehin
oben als Zahl.

**Zwei austauschbare Behälter: es zählt der Vorrat, nicht der Einzelwert.**
Zwei Gasflaschen sind ein Vorrat mit zwei Kammern; eine leere Flasche ist
kein Alarm, solange die andere trägt. Auf der Gasseite deshalb:

| Bedingung | Text | Farbe |
|---|---|---|
| beide < 10 % | `GAS LEER` | rot |
| beide < 25 % | `GAS KNAPP` | orange |
| eine < 10 % | `GAS A LEER` / `GAS I LEER` | grau |

Der graue Fall setzt eine automatische Umschaltung voraus (Truma Duo o.
ä.) — dann ist er ein Hinweis, dass eine Flasche fällig ist, und keine
Aufforderung. Ohne automatische Umschaltung gehört er auf orange, weil
dann jemand raus muss.

---

## 7. Ungültige Werte

Ein Dashboard, das bei fehlender Verbindung den letzten Wert weiterzeigt,
ist gefährlicher als eines, das nichts zeigt. Jedes Label prüft deshalb
selbst und fällt auf `---` in `0x555555` zurück.

```yaml
text: !lambda |-
  #ifdef USE_API
  if (!api_is_connected()) return std::string("---");
  #endif
  if (!id(s_soc).has_state()) return std::string("---");
  return str_sprintf("%.0f%%", x);
```

Die `#ifdef USE_API`-Klammer ist der Trick, der Block C unverändert
übertragbar macht: im Simulator gibt es keinen `api:`-Block, also fällt
die Prüfung weg und man sieht echte Werte; auf dem Gerät greift sie
automatisch. Ohne die Klammer würde der Simulator dauerhaft `---` zeigen.

Der Platzhalter behält die Einheit: `START ---V` und `---%`, nicht `---`.
Sonst springt die Zeilenbreite beim ersten gültigen Wert.

Das gilt auch für **Taster**: ohne Verbindung `PARK ---`, nicht
`PARK AUS`. „Aus" ist eine Aussage über den Zustand des Fahrzeugs, die
man ohne Verbindung nicht belegen kann.

Der im Widget hinterlegte Starttext steht ebenfalls in `0x555555` — sonst
sieht der Platzhalter vor dem ersten Sensorwert aus wie ein gültiger Wert.

Die Fusszeile ist von der `---`-Regel ausgenommen: sie ist im Normalfall
leer, ein `---` dort wäre kein fehlender Wert, sondern ein neuer Zustand.
Sie schreibt stattdessen `KEINE VERBINDUNG` bzw. `KEIN WERT` in
`0x555555`.

---

## 8. Widget-Konventionen

### Taster

| | ein Taster | zwei Taster |
|---|---|---|
| Breite | 104 px | 76 px, `x: ±40` |
| Höhe | 30 px | 30 px |
| Radius | 15 | 15 |

Der Taster ist rechteckig, das Display ist rund: es zählen die **Ecken**,
nicht die Mitte. Bei `y_row 48` liegt die untere Ecke eines 104er Tasters
auf Radius 81.7 — auf einer Doppelring-Seite (Innenring bei 90) noch
sauber. Ab `y_row 56` schneidet er.

Beschriftung als **Kind-Label** mit `align: CENTER`:

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

> Nicht die `text:`-Eigenschaft des Tasters verwenden. Sie ist zwar gültig
> und wird über `lvgl.button.update` gesetzt, hat im Test aber schlechter
> ausgesehen als das Kind-Label. Ebenso `pad_all: 0` weglassen.

Bei zwei Tastern muss die Beschriftung auf drei bis vier Zeichen passen
(`ON` / `CHG` / `INV` / `OFF`, `10 A`). Reicht das nicht, gehört der
zweite Wert nicht in diese Reihe.

Fläche und Rand des Tasters werden über `lvgl.widget.update` gesetzt
(`bg_color`, `border_color`), die Beschriftung über `lvgl.label.update`.

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

Der zweite Ring einer Doppelring-Seite ist derselbe Block mit
`width: 200` / `height: 200`; alles andere bleibt gleich, insbesondere
`arc_width: 10` und die Winkel. Geometrie siehe §4.

Der Arc zeigt immer **0–100 %**, nie eine physikalische Grösse. Wenn die
Grösse keine natürliche Obergrenze hat, wird sie in Prozent einer
sinnvollen Bezugsgrösse umgerechnet (Beispiel Netz: Eingangsstrom in
Prozent der eingestellten Strombegrenzung). Eine feste absolute Skala
führt dazu, dass der Bogen die meiste Zeit fast leer oder fast voll ist.

Wert und Indikatorfarbe gehören in **einen** `lvgl.arc.update`-Aufruf,
nicht in zwei hintereinander:

```yaml
- lvgl.arc.update:
    id: arc_soc
    value: !lambda "return x;"
    indicator:
      arc_color: !lambda "return lv_color_hex(0xE74C3C);"
```

### Hintergrund

`disp_bg_color:` ist abgekündigt, und ein `bg_color:` direkt unter `lvgl:`
deckt nur den Teil ab, den die Seite freilässt. Stattdessen:

```yaml
lvgl:
  default_font: montserrat_16
  bottom_layer:
    bg_color: 0x000000
    bg_opa: COVER
```

---

## 9. Bindings

**Ein Wert, eine Anzeige** → `on_value` direkt am Sensor.

**Mehrere voneinander abhängige Werte** → ein Zeichenskript pro Seite,
das die ganze Seite neu schreibt; jeder Sensor ruft nur `script.execute`:

```yaml
script:
  - id: draw_grid
    mode: restart
    then:
      - lvgl.arc.update: ...
      - lvgl.label.update: ...
```

Grund: sonst stünde nach der Änderung eines Werts die von beiden Werten
abhängige Zeile bis zum nächsten Update des anderen Sensors falsch da.
Im Skript wird über `id(sensor).state` gelesen, nicht über `x`.

Das Zeichenskript gehört zusätzlich in `esphome: on_boot:` mit
`priority: -100`. Sonst steht die Zeile bis zum ersten Sensorwert auf dem
Platzhalter, auf dem Gerät unter Umständen minutenlang.

Fahrzeugfeste Konstanten (Tankgrössen, Flaschengewichte) stehen als
Literal im Skript, mit Kommentar. Nicht in `substitutions:` — die müssen
auf allen Seiten identisch bleiben — und nicht als `globals:`, weil auf
dem Dial kein Zustand gehalten wird. Aktuell: Frisch 180 L, Grau 90 L,
Gasflasche 10.5 kg netto.

---

## 10. Namensschema

| Präfix | Für |
|---|---|
| `page_` | Seite (`page_battery`, `page_grid`) |
| `arc_` | Bogen |
| `lbl_` | Label |
| `btn_` | Taster |
| `s_` | Sensor / Text-Sensor (Datenquelle) |
| `draw_` | Zeichenskript einer Seite |
| `g_sim_` | Global, **nur** in der Simulation |

Bei zwei gleichrangigen Werten unterscheidet ein Suffix die Spalten, und
zwar dasselbe Kürzel wie in der Beschriftung:
`lbl_water_pct_f` / `_g`, `lbl_gas_pct_a` / `_i`. Das gilt bis zum
Sensor durch (`s_gas_a`, `s_gas_i`) — welche Flasche physisch am
Aussenring hängt, entscheidet dann allein die `entity_id`.

Die Seiten-IDs und ihre **Reihenfolge** sind die Navigation — der Encoder
adressiert über den Index. Reihenfolge nur bewusst ändern.

---

## 11. Simulation

* Datenquellen als `platform: template` mit `update_interval`.
* Werte **durchlaufen den ganzen Bereich**, damit alle Farbschwellen ohne
  Warten sichtbar werden (SOC rampt in 4er-Schritten von 100 auf 0, der
  MP-Zustand zykelt inklusive `fault`).
* Zwei Werte einer Seite laufen mit **unterschiedlichem**
  `update_interval`, sonst treten immer dieselben Kombinationen auf und
  man sieht die Rangfolge der Statuszeile nie. Das gilt auch für Werte,
  die nur zusammen in einer Zeile stehen (Spannung und Strom): bei
  gleichem Intervall und gleicher Listenlänge wiederholt sich das Paar.
* Taster ändern nur einen `g_sim_`-Global. Die Geräte-Variante
  (`homeassistant.service`) steht **auskommentiert direkt darunter**.
* Kein `api:`-Block — sonst greift die Ungültigkeitsprüfung.

Der Dial ist auf dem Gerät immer nur Anzeige und Taster. Die Wahrheit
liegt bei Home Assistant beziehungsweise Node-RED; kein Zustand wird
lokal gehalten.

---

## 12. Checkliste Zusammenführen

1. Block A aller Seitendateien verwerfen, Hardware-Datei einsetzen.
2. `substitutions:` **einmal** übernehmen, Werte müssen identisch sein.
   Beim ersten Zusammenführen die Seiten prüfen, die noch auf einem
   älteren Raster stehen — sie ändern sich dabei optisch.
3. Block B: `platform: template` → `platform: homeassistant`, `entity_id`
   eintragen. Sensor-IDs behalten.
4. Taster-`on_click`: Sim-Lambda gegen den auskommentierten
   `homeassistant.service`-Aufruf tauschen.
5. Blöcke C und D unverändert einsetzen, D in der Reihenfolge der
   Seitenindizes.
6. `g_sim_`-Globals entfernen.
7. Alle `on_boot`-Aufrufe der Zeichenskripte in **einen** `on_boot`-Block
   zusammenfassen.
8. Prüfen, dass keine ID doppelt vorkommt und keine Anzeige auf eine
   gelöschte ID zeigt — das ist die häufigste Fehlerquelle.
9. `esphome config` gegen die zusammengeführte Datei laufen lassen,
   **bevor** geflasht wird.

---

## 13. Offene Punkte

* **Farbe des nachrangigen Rings.** `0x9AA0A6` ist gesetzt, aber nur im
  Simulator beurteilt. Am Gerät entscheiden, ob der Ring daneben zu laut
  oder zu leise ist.
* **`GAS A` / `GAS I`.** Die Beschriftung benennt den Ring und setzt
  voraus, dass man „aussen/innen" auf die Ringe bezieht und nicht auf den
  Gaskasten. Am Gerät prüfen, ob das ohne Erklärung trägt.
* **Lesbarkeit von `montserrat_24`** im Zwei-Wert-Layout, aus
  Fahrerposition. Falls zu klein: Literzeile streichen und auf 28 gehen.
* **Beide Alarme gleichzeitig.** Die Statuszeile zeigt nur den höheren.
  Ob das reicht oder ob es einen kombinierten Text braucht, zeigt sich
  erst im Betrieb.
* **Bestätigung für gefährliche Taster.** `MP OFF` nimmt Landstrom,
  Ladung und 230 V weg; `RETRACT` auf der Nivellierungsseite fährt
  Stützen ein. Beides sollte einen langen Druck oder eine Rückfrage
  brauchen, nicht einen zweiten Klick im Durchschalten.
* **Ebene 2 mit zwei Tastern.** Der Encoder muss zwischen den Tastern
  einer Reihe wechseln können, nicht nur einen Wert verstellen.
* **Sonderzeichen.** `°` wird auf der Temperatur- und Boilerseite
  gebraucht; bei den internen montserrat-Schriften ist es enthalten, bei
  einer eigenen Schrift müsste es in die Glyphenliste. Der Mittelpunkt
  `·` ist nicht geprüft und wird bis dahin vermieden.
* **Optische Höhe des Hauptwerts.** `72%` und `540 W` stehen auf
  demselben `y_main`, wirken aber unterschiedlich hoch, weil das
  Prozentzeichen weiter nach oben reicht. Erst beim echten Durchblättern
  entscheiden, ob das stört.
