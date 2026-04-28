# Streamlit Live Temperatur

Diese App zeigt eine **sehr einfache Live-Messung** mit Streamlit:

- DS18B20-Temperatur an GP2
- interne RP2040-Temperatur
- Board-LED ein- und ausschalten

## Starten

```powershell
uv sync
uv run streamlit run streamlit_live_temp/app.py
```

## Was die App macht

- baut ueber `mpremote` eine Verbindung zum Pico auf
- haelt die Verbindung ueber `my_pico.py` offen
- liest DS18B20 und interne Pico-Temperatur
- aktualisiert zwei getrennte Live-Diagramme
- zeigt die Live-Diagramme untereinander mit Matplotlib
- startet und stoppt die Live-Messung per Button
- schaltet die Board-LED per `LED ein` und `LED aus`
- kann mit einem Messintervall ab `0.2 s` laufen

## Verschaltung

Die App erwartet den DS18B20 standardmaessig an `GP2`.

![Aktuelle DS18B20-Verschaltung](../documentation/PXL_20260428_125258174.MP.jpg)

Kurzfassung:

- DS18B20 `GND` -> Pico `GND`
- DS18B20 `VDD` -> Pico `3V3(OUT)`
- DS18B20 `DQ` -> Pico `GP2`
- `4.7 kOhm` Pull-up-Widerstand zwischen `DQ` und `3V3(OUT)`

## Verwendete Pakete und warum

- `streamlit`
  - fuer die Web-Oberflaeche (Buttons, Sidebar, Live-Plot, Status)
  - schnellster Weg fuer eine einfache Live-Ansicht ohne Frontend-Setup

- `mpremote`
  - offizielles MicroPython-Tool, um Code ueber USB auf dem Pico auszufuehren
  - wird im Backend `my_pico.py` fuer die dauerhafte Verbindung genutzt

- `sys` (Python-Standardbibliothek)
  - macht den Projektordner fuer `import my_pico` auffindbar

- `time` (Python-Standardbibliothek)
  - steuert das Messintervall ueber `sleep`

## Hinweise

- Pico muss per USB verbunden sein und MicroPython installiert haben.
- Beim ersten Streamlit-Start kann eine E-Mail-Abfrage erscheinen; einfach leer lassen und mit Enter bestaetigen.
- `Port = auto` funktioniert meist direkt.
- Falls noetig, einen festen Port setzen (z. B. `COM4`).
- Fuer `0.2 s` Messintervall nutzt die App standardmaessig 10 Bit DS18B20-Aufloesung.
- Die Formel fuer `temp_c` ist die uebliche RP2040-Naehungsformel und dient als schneller Start.
