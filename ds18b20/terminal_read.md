## Temperatur einfach im Notebook lesen

Das Modul `my_pico.py` liegt im Projektordner. Im Notebook kann es so benutzt werden:

```python
import my_pico

pico = my_pico.connect("auto")
temp = my_pico.get_temp(pico)

print(temp)
```

Wenn du fertig bist:

```python
my_pico.disconnect(pico)
```

Wichtig: `get_temp()` fuehrt jedes Mal neu `convert_temp()` aus und wartet kurz,
damit wirklich ein neuer Messwert vom DS18B20 gelesen wird.
