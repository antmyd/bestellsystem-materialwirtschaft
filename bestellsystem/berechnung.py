"""M6 Meldebestand, M7 Losgröße (Andler), M8 Kennzahlen, M9 Bestellprüfung."""

from __future__ import annotations

import math
from dataclasses import dataclass


def tagesbedarf(jahresbedarf: float, arbeitstage_pro_jahr: int) -> float:
    """Tagesbedarf = Jahresbedarf / Arbeitstage pro Jahr."""
    if arbeitstage_pro_jahr <= 0:
        raise ValueError("Arbeitstage pro Jahr müssen größer als 0 sein")
    return jahresbedarf / arbeitstage_pro_jahr


def lieferzeit_in_tagen(lieferzeit_wochen: float, arbeitstage_pro_woche: int) -> float:
    """Lieferzeit in Arbeitstagen = Wochen × Arbeitstage pro Woche."""
    return lieferzeit_wochen * arbeitstage_pro_woche


def meldebestand(tagesbedarf_: float, lieferzeit_tage: float, sicherheitsbestand: float) -> float:
    """Meldebestand = (Tagesbedarf × Lieferzeit in Tagen) + Sicherheitsbestand."""
    return tagesbedarf_ * lieferzeit_tage + sicherheitsbestand


def andler_losgroesse(bestellkosten: float, jahresbedarf: float,
                      lagerhaltungskosten: float) -> float:
    """Optimale Bestellmenge Q = Wurzel(2 × Kb × D / H)."""
    if bestellkosten <= 0 or jahresbedarf <= 0 or lagerhaltungskosten <= 0:
        raise ValueError("Kb, D und H müssen größer als 0 sein")
    return math.sqrt(2 * bestellkosten * jahresbedarf / lagerhaltungskosten)


def aufrunden(menge: float) -> int:
    """Bestellmengen werden auf ganze Stück aufgerundet."""
    return math.ceil(round(menge, 9))


@dataclass
class Kennzahlen:
    bestellhaeufigkeit: float          # Bestellungen pro Jahr
    bestellzyklus_tage: float          # Arbeitstage zwischen zwei Bestellungen
    durchschnittlicher_bestand: float  # Stück
    reichweite_tage: float             # Tage, die der aktuelle Bestand reicht
    bestellkosten_jahr: float          # EUR
    lagerkosten_jahr: float            # EUR, inkl. Sicherheitsbestand
    lagerkosten_sicherheitsbestand: float  # EUR, Anteil des Sicherheitsbestands
    gesamtkosten_jahr: float           # EUR
    kapitalbindung: float              # EUR

    def als_dict(self) -> dict[str, float]:
        return dict(self.__dict__)


def kennzahlen(jahresbedarf: float, losgroesse: float, bestellkosten: float,
               lagerhaltungskosten: float, sicherheitsbestand: float,
               wert: float, arbeitstage_pro_jahr: int, lagerbestand: float) -> Kennzahlen:
    """Größen des Bestandsverlaufs bei gegebener Bestellmenge."""
    if losgroesse <= 0:
        raise ValueError("Bestellmenge muss größer als 0 sein")
    td = tagesbedarf(jahresbedarf, arbeitstage_pro_jahr)
    haeufigkeit = jahresbedarf / losgroesse
    durchschnitt = losgroesse / 2 + sicherheitsbestand
    bestellkosten_jahr = haeufigkeit * bestellkosten
    lagerkosten_jahr = durchschnitt * lagerhaltungskosten
    return Kennzahlen(
        bestellhaeufigkeit=haeufigkeit,
        bestellzyklus_tage=arbeitstage_pro_jahr / haeufigkeit,
        durchschnittlicher_bestand=durchschnitt,
        reichweite_tage=lagerbestand / td if td > 0 else math.inf,
        bestellkosten_jahr=bestellkosten_jahr,
        lagerkosten_jahr=lagerkosten_jahr,
        lagerkosten_sicherheitsbestand=sicherheitsbestand * lagerhaltungskosten,
        gesamtkosten_jahr=bestellkosten_jahr + lagerkosten_jahr,
        kapitalbindung=durchschnitt * wert,
    )


@dataclass
class Pruefergebnis:
    bestellen: bool
    menge: float
    disponibler_bestand: float
    tage_bis_meldebestand: float
    text: str


def bestellpruefung(lagerbestand: float, offene_bestellungen: float,
                    meldebestand_: float, losgroesse: int,
                    tagesbedarf_: float) -> Pruefergebnis:
    """Meldebestandsverfahren: bestellen, wenn disponibler Bestand <= Meldebestand."""
    disponibel = lagerbestand + offene_bestellungen
    if disponibel <= meldebestand_:
        return Pruefergebnis(True, losgroesse, disponibel, 0.0,
                             f"Meldebestand erreicht: {losgroesse} Stück bestellen")
    tage = (disponibel - meldebestand_) / tagesbedarf_ if tagesbedarf_ > 0 else math.inf
    tage_text = f"{tage:.1f}".replace(".", ",")
    return Pruefergebnis(False, 0, disponibel, tage,
                         f"keine Bestellung; Meldebestand in ca. {tage_text} Arbeitstagen erreicht")


def zykluszeit_bestellmenge(tagesbedarf_: float, bestellzyklus_tage: float,
                            lieferzeit_tage: float, sicherheitsbestand: float,
                            lagerbestand: float, offene_bestellungen: float) -> tuple[float, int]:
    """Zykluszeitverfahren: zum festen Zeitpunkt auf den Höchstbestand auffüllen.

    Höchstbestand = Tagesbedarf × (Bestellzyklus + Lieferzeit) + Sicherheitsbestand
    Bestellmenge  = Höchstbestand − disponibler Bestand (mindestens 0)
    """
    hoechstbestand = tagesbedarf_ * (bestellzyklus_tage + lieferzeit_tage) + sicherheitsbestand
    menge = max(0.0, hoechstbestand - (lagerbestand + offene_bestellungen))
    return hoechstbestand, aufrunden(menge)
