"""M10 Ausgabe: Ergebnistabellen, Bestellvorschläge und Rechenprotokoll als Text."""

from __future__ import annotations

from .ablauf import Lauf
from .protokoll import zahl


def tabelle(kopf: list[str], zeilen: list[list[str]], rechts: set[int] = frozenset()) -> str:
    breiten = [max(len(str(z[i])) for z in [kopf] + zeilen) for i in range(len(kopf))]

    def format_zeile(zeile: list[str]) -> str:
        teile = []
        for i, zelle in enumerate(zeile):
            zelle = str(zelle)
            teile.append(zelle.rjust(breiten[i]) if i in rechts else zelle.ljust(breiten[i]))
        return " | ".join(teile).rstrip()

    trenner = "-+-".join("-" * b for b in breiten)
    return "\n".join([format_zeile(kopf), trenner] + [format_zeile(z) for z in zeilen])


def bericht(lauf: Lauf, mit_protokoll: bool = True) -> str:
    teile: list[str] = []
    p = lauf.parameter
    teile.append("BESTELLSYSTEM – ERGEBNISBERICHT")
    teile.append(f"Parameter: {p.arbeitstage_pro_jahr} Arbeitstage/Jahr, "
                 f"{p.arbeitstage_pro_woche} Arbeitstage/Woche, "
                 f"ABC-Grenzen {zahl(p.abc_grenze_a * 100)} % / {zahl(p.abc_grenze_b * 100)} %, "
                 f"XYZ-Grenzen {zahl(p.xyz_grenze_x, 1, fest=True)} / "
                 f"{zahl(p.xyz_grenze_y, 1, fest=True)}")

    if lauf.mengenstuecklisten:
        for erzeugnis, liste in lauf.mengenstuecklisten.items():
            teile.append(f"\nMengenstückliste {erzeugnis} (je Stück)")
            teile.append(tabelle(["Bezeichnung", "Menge"],
                                 [[t, zahl(m)] for t, m in liste.items()], {1}))

    if lauf.abc:
        teile.append("\nABC-Analyse")
        teile.append(tabelle(
            ["Nummer", "Wert EUR", "Verbrauch", "Verbrauchswert EUR", "Anteil %", "kum. %", "Klasse"],
            [[z.nummer, zahl(z.wert), zahl(z.verbrauch), zahl(z.verbrauchswert),
              zahl(z.anteil * 100, fest=True), zahl(z.anteil_kumuliert * 100, fest=True), z.klasse]
             for z in lauf.abc],
            {1, 2, 3, 4, 5}))

    if lauf.xyz:
        teile.append("\nXYZ-Analyse")
        teile.append(tabelle(
            ["Nummer", "Mittelwert", "Std.-abw.", "VK", "Klasse"],
            [[z.nummer, zahl(z.mittelwert), zahl(z.standardabweichung),
              zahl(z.variationskoeffizient, 3), z.klasse] for z in lauf.xyz],
            {1, 2, 3}))

    teile.append("\nBestellverfahren und Bestellvorschläge")
    zeilen = []
    for e in lauf.ergebnisse:
        zeilen.append([
            e.nummer,
            f"{e.abc or '-'}{e.xyz or '-'}",
            e.verfahren or "-",
            zahl(e.meldebestand) if e.meldebestand is not None else "-",
            str(e.losgroesse) if e.losgroesse is not None else "-",
            zahl(e.bestellvorschlag) if e.bestellvorschlag else "-",
            e.status,
        ])
    teile.append(tabelle(["Nummer", "Klasse", "Verfahren", "Meldebestand", "Q", "Bestellen", "Status"],
                         zeilen, {3, 4, 5}))

    hinweise = [(e.nummer, h) for e in lauf.ergebnisse for h in e.hinweise]
    if hinweise:
        teile.append("\nHinweise")
        teile.extend(f"- {nr}: {h}" for nr, h in hinweise)

    if mit_protokoll:
        teile.append("\nRechenprotokoll")
        teile.append(lauf.protokoll.als_text())
    return "\n".join(teile)
