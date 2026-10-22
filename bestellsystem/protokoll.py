"""Rechenprotokoll: macht jeden Rechenschritt nachvollziehbar."""

from __future__ import annotations

from dataclasses import dataclass


def zahl(wert: float, stellen: int = 2, fest: bool = False) -> str:
    """Zahl im deutschen Format: 12.000 bzw. 692,82.

    Ganze Zahlen werden ohne Nachkommastellen ausgegeben, außer bei fest=True
    (z. B. Prozentspalten, damit alle Zeilen gleich aussehen).
    """
    if not fest and abs(wert) < 1e15 and abs(wert - round(wert)) < 1e-9:
        text = f"{round(wert):,}"
    else:
        text = f"{wert:,.{stellen}f}"
    if text.startswith("-") and text.strip("-0.,") == "":
        text = text[1:]
    return text.replace(",", "X").replace(".", ",").replace("X", ".")


@dataclass
class Eintrag:
    modul: str
    material: str
    groesse: str
    formel: str
    rechnung: str
    ergebnis: str


class Protokoll:
    """Sammelt Einträge in der Reihenfolge, in der gerechnet wurde."""

    def __init__(self) -> None:
        self.eintraege: list[Eintrag] = []

    def schreibe(self, modul: str, material: str, groesse: str,
                 formel: str, rechnung: str, ergebnis: str) -> None:
        self.eintraege.append(Eintrag(modul, material, groesse, formel, rechnung, ergebnis))

    def fuer(self, material: str) -> list[Eintrag]:
        return [e for e in self.eintraege if e.material == material]

    def als_text(self) -> str:
        zeilen = []
        for e in self.eintraege:
            zeile = f"[{e.modul}] {e.material}: {e.groesse}"
            if e.formel:
                zeile += f" = {e.formel}"
            if e.rechnung:
                zeile += f" = {e.rechnung}"
            zeile += f" -> {e.ergebnis}"
            zeilen.append(zeile)
        return "\n".join(zeilen)
