# Bestellsystem – Materialwirtschaft / Beschaffung

Kleines Bestellsystem für die Lehrveranstaltung *Produktionswirtschaft / Logistik* (HTW Berlin, Bachelor WI).
Es rechnet die Verfahren aus Vorlesung und Übung durch und protokolliert jeden Rechenschritt mit
Formel, eingesetzten Werten und Ergebnis.

- reines Python (ab 3.10), **keine externen Pakete**
- Eingabe als JSON-Datei, Ausgabe als Textbericht
- 37 Tests, die die Musterlösungen der Übungen nachrechnen

## Starten

```bash
python -m bestellsystem daten/beispiel.json                   # Bericht mit Rechenprotokoll
python -m bestellsystem daten/beispiel.json --ohne-protokoll  # nur Ergebnistabellen
python -m unittest discover -s tests -t .                     # Tests
```

## Programmablauf (Module)

```
M1 Datenerfassung und Validierung
        │
M2 Bedarfsermittlung  (programmgebunden / verbrauchsgebunden / subjektiv)
        │
   ┌────┴────┐
M3 ABC     M4 XYZ
   └────┬────┘
M5 Bestellverfahren wählen (ABC-XYZ-Matrix, auslösendes Moment)
        │
        ├── Bereitstellverfahren / Bestellung nach Bedarf / einmalige Bestellung ──► M10
        │
        ▼  nur Meldebestands- und Zykluszeitverfahren
M6 Meldebestand ─► M7 Losgröße (Andler) ─► M8 Kennzahlen
        │
M9 Bestellprüfung
        │
M10 Ausgabe: Bestellvorschläge und Rechenprotokoll
```

| Modul | Datei | Inhalt |
| --- | --- | --- |
| M1 | `ablauf.py` → `validiere` | Prüfregeln: Pflichtfelder, Werte > 0, doppelte Nummern, Begründung bei manueller Vorgabe |
| M2 | `bedarf.py` | Stücklistenauflösung (Baukasten- → Mengenstückliste), Dispositionsstufen, verbrauchsgebundener Bedarf |
| M3 | `analyse.py` → `abc_analyse` | Verbrauchswert = Wert × Verbrauch, Anteil, kumulierter Anteil, Klassen A/B/C |
| M4 | `analyse.py` → `xyz_analyse` | Variationskoeffizient = Standardabweichung / Mittelwert, Klassen X/Y/Z |
| M5 | `bestellverfahren.py` | Strategie aus der ABC-XYZ-Matrix, Bestellverfahren und auslösendes Moment |
| M6–M9 | `berechnung.py` | Meldebestand, Andler-Formel, Kennzahlen des Bestandsverlaufs, Bestellprüfung |
| M10 | `ausgabe.py` | Ergebnistabellen, Hinweise, Rechenprotokoll |
| – | `protokoll.py` | sammelt alle Rechenschritte |
| – | `daten.py`, `__main__.py` | JSON einlesen, Kommandozeile |

## Formeln

| Größe | Formel |
| --- | --- |
| Verbrauchswert | Wert × Verbrauch |
| Variationskoeffizient (VK) | Standardabweichung / Mittelwert |
| Tagesbedarf | Jahresbedarf / Arbeitstage pro Jahr |
| Meldebestand | Tagesbedarf × Lieferzeit in Tagen + Sicherheitsbestand |
| Optimale Bestellmenge (Andler) | Q = √(2 × Kb × D / H) |
| Bestellhäufigkeit | D / Q |
| Bestellzyklus | Arbeitstage pro Jahr / Bestellhäufigkeit |
| durchschnittlicher Bestand | Q / 2 + Sicherheitsbestand |
| Reichweite | Lagerbestand / Tagesbedarf |
| Bestellkosten pro Jahr | D / Q × Kb |
| Lagerhaltungskosten pro Jahr | (Q / 2 + Sicherheitsbestand) × H |
| Höchstbestand (Zykluszeitverfahren) | Tagesbedarf × (Bestellzyklus + Lieferzeit) + Sicherheitsbestand |

## Entscheidungsregeln

**ABC-Klassen:** maßgeblich ist der kumulierte Anteil *vor* dem Artikel (< 80 % → A, < 95 % → B, sonst C).
Der Artikel, der eine Grenze überschreitet, bleibt in der oberen Klasse. Nur so ergibt sich die Einteilung
der Musterlösung (1009 mit 80,003 % → A, 1001 mit 95,02 % → B).

**XYZ-Klassen:** VK < 0,5 → X, VK < 1 → Y, sonst Z. Damit fällt kein Wert zwischen 0,49 und 0,5 durch.
Bei einer Verbrauchsreihe wird die Standardabweichung der Grundgesamtheit verwendet.

**Bestellverfahren (Vorschlag, manuell überschreibbar mit Begründung):**

| | A | B / C |
| --- | --- | --- |
| X / Y | JIT/JIS → Bereitstellverfahren (auslösendes Moment: Verbrauch) | Bestellung nach Verbrauch → Meldebestandsverfahren (Bestand) |
| Z | Bestellung nach Bedarf | einmalige Bestellung, wenn notwendig |

Das Zykluszeitverfahren (auslösendes Moment: Zeitpunkt) wird per Vorgabe gewählt, z. B. um Bestellungen
mehrerer C-Teile beim selben Lieferanten zu bündeln.

**Rundung:** Bestellmengen werden auf ganze Stück aufgerundet; der ungerundete Wert steht im Protokoll.

## Zielkonflikt

Große Bestellmengen senken die Bestellkosten (weniger Bestellungen), erhöhen aber durchschnittlichen Bestand,
Kapitalbindung und Lagerhaltungskosten. Die Andler-Formel findet das Kostenminimum; dort sind Bestellkosten und
Lagerhaltungskosten (ohne Sicherheitsbestand) gleich hoch. Der Bericht weist beide Kostenarten und die Kosten
des Sicherheitsbestands getrennt aus.

**Grenzen:** Die Andler-Formel setzt konstanten Bedarf, konstante Lieferzeit, keine Mengenrabatte und keine
Fehlmengen voraus. Für Y- und Z-Material ist das Ergebnis nur ein Richtwert.

## Eingabedatei

```json
{
  "parameter":   { "arbeitstage_pro_jahr": 240, "arbeitstage_pro_woche": 5 },
  "materialien": [
    { "nummer": "1009", "wert": 37.85, "jahresbedarf": 12000,
      "bestellkosten": 100, "lagerhaltungskosten": 5, "lieferzeit_wochen": 2,
      "sicherheitsbestand": 200, "lagerbestand": 650,
      "verbrauchsreihe": [1000, 990, 1010],
      "verfahren_vorgabe": "Meldebestandsverfahren", "begruendung": "..." }
  ],
  "stueckliste":   { "Material X": { "Bauteil A": 2, "Teil c": 5, "Bauteil B": 3 } },
  "primaerbedarf": { "Material X": 100 }
}
```

Fehlt `jahresbedarf`, wird er aus der Stückliste (programmgebunden) oder aus der Verbrauchsreihe
(verbrauchsgebunden) ermittelt. Das vollständige Beispiel mit den Daten aus den Übungen liegt in
`daten/beispiel.json`; Artikel 1009 trägt dort die Werte der Übung *Beschaffung*.

## Testfälle aus den Übungen

| Übung | Erwartet | Test |
| --- | --- | --- |
| Stücklisten, Material X | Mengenstückliste A 2, B 5, a 25, b 15, c 9; Dispositionsstufen | `tests/test_bedarf.py` |
| ABC-Analyse | 1007, 1009 → A; 1004, 1006, 1001 → B; Rest C; Summe 1.248.700 EUR | `tests/test_analyse.py` |
| XYZ-Analyse | a) 0,2 X, b) 0,2 X, c) 1,167 Z | `tests/test_analyse.py` |
| Beschaffung Teil 2 | Tagesbedarf 50, Meldebestand 700 | `tests/test_berechnung.py` |
| Beschaffung Teil 3 | Q = 692,82 ≈ 693 | `tests/test_berechnung.py` |
