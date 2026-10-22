"""M3 ABC-Analyse und M4 XYZ-Analyse."""

from __future__ import annotations

from statistics import fmean, pstdev

from .modelle import AbcZeile, Parameter, XyzZeile
from .protokoll import Protokoll, zahl


def abc_klasse(anteil_kumuliert_vorher: float, parameter: Parameter) -> str:
    """Klasse nach dem kumulierten Anteil VOR dem Artikel.

    Der Artikel, mit dem eine Grenze überschritten wird, gehört noch zur
    oberen Klasse. So entsteht die Einteilung der Musterlösung
    (1009 mit 80,003 % ist A, 1001 mit 95,02 % ist B).
    """
    if anteil_kumuliert_vorher < parameter.abc_grenze_a:
        return "A"
    if anteil_kumuliert_vorher < parameter.abc_grenze_b:
        return "B"
    return "C"


def abc_analyse(artikel: list[tuple[str, float, float]],
                parameter: Parameter = Parameter(),
                protokoll: Protokoll | None = None) -> list[AbcZeile]:
    """ABC-Analyse.

    artikel: Liste von (Nummer, Wert je Einheit, Verbrauch)
    Schritte: Verbrauchswert = Wert × Verbrauch, absteigend sortieren,
    Anteil in %, kumulierter Anteil, Einteilung in Klassen.
    """
    if not artikel:
        return []
    zeilen = [(nr, wert, verbrauch, wert * verbrauch) for nr, wert, verbrauch in artikel]
    summe = sum(z[3] for z in zeilen)
    if summe <= 0:
        raise ValueError("Summe der Verbrauchswerte muss größer als 0 sein")
    zeilen.sort(key=lambda z: z[3], reverse=True)

    ergebnis: list[AbcZeile] = []
    kumuliert = 0.0
    for nr, wert, verbrauch, verbrauchswert in zeilen:
        anteil = verbrauchswert / summe
        klasse = abc_klasse(kumuliert, parameter)
        kumuliert += anteil
        ergebnis.append(AbcZeile(nr, wert, verbrauch, verbrauchswert, anteil, kumuliert, klasse))
        if protokoll:
            protokoll.schreibe("M3", nr, "Verbrauchswert", "Wert × Verbrauch",
                               f"{zahl(wert)} × {zahl(verbrauch)}", f"{zahl(verbrauchswert)} EUR")
            protokoll.schreibe("M3", nr, "Anteil / kumuliert",
                               "Verbrauchswert / Summe der Verbrauchswerte",
                               f"{zahl(verbrauchswert)} / {zahl(summe)}",
                               f"{zahl(anteil * 100, fest=True)} % / "
                               f"{zahl(kumuliert * 100, fest=True)} % -> Klasse {klasse}")
    return ergebnis


def variationskoeffizient(mittelwert: float, standardabweichung: float) -> float:
    """VK = Standardabweichung / Mittelwert."""
    if mittelwert == 0:
        raise ValueError("Mittelwert ist 0: Variationskoeffizient nicht berechenbar")
    return standardabweichung / mittelwert


def xyz_klasse(vk: float, parameter: Parameter = Parameter()) -> str:
    """X: 0–0,49 (konstant), Y: 0,5–0,99 (schwankend), Z: ab 1 (sporadisch)."""
    if vk < parameter.xyz_grenze_x:
        return "X"
    if vk < parameter.xyz_grenze_y:
        return "Y"
    return "Z"


def xyz_analyse(nummer: str, verbrauchsreihe: list[float],
                parameter: Parameter = Parameter(),
                protokoll: Protokoll | None = None) -> XyzZeile:
    """XYZ-Analyse aus einer Verbrauchsreihe.

    Die Standardabweichung wird für die Grundgesamtheit berechnet
    (alle Perioden des Betrachtungszeitraums liegen vor).
    """
    if len(verbrauchsreihe) < 2:
        raise ValueError("Für die XYZ-Analyse sind mindestens 2 Verbrauchswerte nötig")
    mittelwert = fmean(verbrauchsreihe)
    std = pstdev(verbrauchsreihe)
    vk = variationskoeffizient(mittelwert, std)
    klasse = xyz_klasse(vk, parameter)
    if protokoll:
        protokoll.schreibe("M4", nummer, "Variationskoeffizient",
                           "Standardabweichung / Mittelwert",
                           f"{zahl(std)} / {zahl(mittelwert)}",
                           f"{zahl(vk, 3)} -> Klasse {klasse}")
    return XyzZeile(nummer, mittelwert, std, vk, klasse)
