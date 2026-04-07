# RaspyPico Minimal Setup

Dieses Projekt ist absichtlich minimal:

- USB-Verbindung zum Raspberry Pi Pico (MicroPython)
- Code aus einem Notebook auf dem Pico ausfuehren
- LED-Blink-Test

## 1) Voraussetzungen

- Raspberry Pi Pico ist per USB angeschlossen.
- Auf dem Pico laeuft **MicroPython**.

### MicroPython auf den Pico flashen (Windows)

1. Passende Download-Seite waehlen:
   - Raspberry Pi Pico: https://micropython.org/download/RPI_PICO/
2. Auf der Seite unter **Releases** die neueste `.uf2` Datei herunterladen.
3. Pico vom USB trennen.
4. **BOOTSEL-Taste** auf dem Board gedrueckt halten.
   - Die Taste ist auf dem Board mit `BOOTSEL` beschriftet (nahe USB-Anschluss).
5. Waehrend die Taste gedrueckt ist, Pico per USB wieder anschliessen.
6. Taste loslassen, sobald in Windows ein neues Laufwerk (meist `RPI-RP2`) erscheint.
7. Die heruntergeladene `.uf2` Datei auf dieses Laufwerk kopieren.
8. Nach dem Kopieren startet der Pico automatisch neu und das `RPI-RP2` Laufwerk verschwindet wieder.

Danach sollte der Pico als serieller Port (COMx) auftauchen.

## 2) Umgebung installieren

```powershell
uv sync
.\.venv\Scripts\Activate.ps1

```
Und acuh diese Umgebung im Notebook als Jupyter Kernel aktivieren

`uv sync` installiert auch `mpremote` (wird im Notebook genutzt, um Code auf dem Pico auszufuehren).

## Was ist `mpremote`?

`mpremote` ist das offizielle MicroPython-CLI-Tool, um ein Board (z. B. Pico) ueber USB/Serial fernzusteuern.
Damit kann man unter anderem:

- Geraete finden: `mpremote connect list`
- Ein Geraet verbinden (automatisch): `mpremote connect auto ...`
- Python-Code direkt auf dem Pico ausfuehren: `mpremote exec "print('hello')"`
- Dateien auf das Board kopieren und verwalten

Offizielle Doku:
- https://docs.micropython.org/en/latest/reference/mpremote.html

## 3) Notebook starten

- `test_pico.ipynb` oeffnen
- Kernel: **Python (raspypico)** waehlen
- Zellen von oben nach unten ausfuehren

## Hinweise

- Wenn keine Verbindung gefunden wird, zeigt die erste Notebook-Zelle die Ausgabe von `mpremote connect list`.
- Der LED-Test nutzt `Pin("LED")` und faellt auf `Pin(25)` zurueck.

## Was bei `run_on_pico(...)` passiert

Im Notebook wird ein Python-String gebaut, zum Beispiel:

```python
code = f'''
...
print(f"{{t:.3f}},{{raw}},{{temp_c:.2f}}")
...
'''
out, err = run_on_pico(code, port=port, exec_timeout_s=20)
```

Wichtig:

- Dieser `code`-String wird auf dem **Pico** ausgefuehrt, nicht im Notebook-Kernel.
- `run_on_pico(...)` ruft intern `python -m mpremote connect auto exec <code>` auf.
- `out` ist die Text-Ausgabe vom Pico (stdout), `err` sind Fehlermeldungen (stderr).
- Zum schnellen Verstehen reicht oft:

```python
print(out)
```

Warum `{{...}}` im inneren `print(f"...")`?

- Der aeussere String ist schon ein `f'''...'''` im Notebook.
- Mit doppelten Klammern bleiben die Platzhalter fuer den Pico erhalten.
- Ohne doppelte Klammern versucht das Notebook, z. B. `{t}`, selbst auszuwerten (`NameError` moeglich).

## LED ein/aus schalten und Temperatur lesen im Terminal

'
PS C:\Users\UlrichLehre\Documents\RaspyPico> & c:\Users\UlrichLehre\Documents\RaspyPico\.venv\Scripts\Activate.ps1
(raspypico-notebook) PS C:\Users\UlrichLehre\Documents\RaspyPico> mpremote connect auto
Connected to MicroPython at COM4
Use Ctrl-] or Ctrl-x to exit this shell
MicroPython v1.28.0 on 2026-04-06; Raspberry Pi Pico with RP2040
Type "help()" for more information.
>>> from machine import Pin

>>> led = Pin("LED", Pin.OUT)

>>> led.toggle()

>>> led.toggle()

>>> from machine import ADC

>>> sensor = ADC(4)

>>> raw = sensor.read_u16()

>>> print(raw)
14195

>>> voltage = raw * 3.3 / 65535

>>> temp_c = 27 - (voltage - 0.706) / 0.001721

>>> print(temp_c)

21.894816
>>>

## Pin Diagramm

[https://circuitstate.com/wp-content/uploads/2022/12/Raspberry-Pi-Pico-Pinout-Diagram-r0.3-CIRCUITSTATE-Electronics-01.png](https://circuitstate.com/wp-content/uploads/2022/12/Raspberry-Pi-Pico-Pinout-Diagram-r0.3-CIRCUITSTATE-Electronics-01.png)

Oder Internet Suche nach ` raspberry pico pin diagram official `

## Anleitung zum internen Temperatur Sensor

[Anleitung im Temperatur Kompendium](https://www.elektronik-kompendium.de/sites/raspberry-pi/2612121.htm)

