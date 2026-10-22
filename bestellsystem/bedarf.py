"""M2 Bedarfsermittlung.

- programmgebunden (deterministisch, "rechnen"): Stücklistenauflösung
- verbrauchsgebunden (stochastisch, "schätzen"): Mittelwert der Verbrauchsreihe
- subjektiv (heuristisch, "raten"): manuelle Eingabe mit Begründung (siehe ablauf)

Eine Stückliste wird als Sammlung von Baukastenstücklisten gespeichert:
    {"Material X": {"Bauteil A": 2, "Teil c": 5, "Bauteil B": 3},
     "Bauteil A":  {"Bauteil B": 1, "Teil c": 2},
     "Bauteil B":  {"Teil a": 5, "Teil b": 3}}
"""

from __future__ import annotations

from statistics import fmean

from .protokoll import Protokoll, zahl

Stueckliste = dict[str, dict[str, float]]


class StuecklistenFehler(ValueError):
    """Ungültige Stückliste, z. B. ein Teil, das in sich selbst eingeht."""


def baukastenstueckliste(stueckliste: Stueckliste, teil: str) -> dict[str, float]:
    """Direkte Bestandteile eines Teils (nur die erste Fertigungsstufe darunter)."""
    return dict(stueckliste.get(teil, {}))


def dispositionsstufen(stueckliste: Stueckliste, erzeugnis: str) -> dict[str, int]:
    """Dispositionsstufe je Teil = unterste Stufe, auf der das Teil vorkommt.

    Mehrfach verwendete Teile werden auf die unterste Stufe gezogen.
    """
    stufen: dict[str, int] = {}

    def besuche(teil: str, stufe: int, pfad: tuple[str, ...]) -> None:
        if teil in pfad:
            kreis = " -> ".join(pfad + (teil,))
            raise StuecklistenFehler(f"Zyklus in der Stückliste: {kreis}")
        stufen[teil] = max(stufen.get(teil, 0), stufe)
        for kind in stueckliste.get(teil, {}):
            besuche(kind, stufe + 1, pfad + (teil,))

    besuche(erzeugnis, 0, ())
    return stufen


def mengenstueckliste(stueckliste: Stueckliste, erzeugnis: str,
                      menge: float = 1.0,
                      protokoll: Protokoll | None = None) -> dict[str, float]:
    """Löst die Stückliste auf und liefert den Gesamtbedarf je Teil.

    Die Teile werden Dispositionsstufe für Dispositionsstufe von oben nach
    unten abgearbeitet. Ein Teil wird erst aufgelöst, wenn alle Bedarfe aus
    den übergeordneten Teilen bekannt sind; gleiche Teile werden dabei
    zusammengefasst.
    """
    stufen = dispositionsstufen(stueckliste, erzeugnis)
    bedarf: dict[str, float] = {erzeugnis: menge}

    for teil in sorted(stufen, key=lambda t: (stufen[t], t)):
        teilbedarf = bedarf.get(teil, 0.0)
        for kind, menge_je_teil in stueckliste.get(teil, {}).items():
            zusatz = teilbedarf * menge_je_teil
            bedarf[kind] = bedarf.get(kind, 0.0) + zusatz
            if protokoll:
                protokoll.schreibe(
                    "M2", kind, f"Sekundärbedarf aus {teil}",
                    f"Bedarf {teil} × Menge je {teil}",
                    f"{zahl(teilbedarf)} × {zahl(menge_je_teil)}",
                    f"+{zahl(zusatz)} (Summe {zahl(bedarf[kind])})")

    del bedarf[erzeugnis]
    return dict(sorted(bedarf.items(), key=lambda kv: (stufen[kv[0]], kv[0])))


def verbrauchsgebundener_bedarf(verbrauchsreihe: list[float],
                                perioden_pro_jahr: int = 12) -> float:
    """Prognose des Jahresbedarfs aus dem Durchschnitt der Vergangenheit."""
    if not verbrauchsreihe:
        raise ValueError("Verbrauchsreihe ist leer")
    return fmean(verbrauchsreihe) * perioden_pro_jahr
