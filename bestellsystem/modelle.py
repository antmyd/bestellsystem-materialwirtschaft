"""Datenmodell: Parameter, Materialstamm und Ergebnisse."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Parameter:
    """Globale Parameter, die für alle Materialien gelten."""

    arbeitstage_pro_jahr: int = 240
    arbeitstage_pro_woche: int = 5
    # ABC-Grenzen als kumulierter Anteil am Gesamtverbrauchswert
    abc_grenze_a: float = 0.80
    abc_grenze_b: float = 0.95
    # XYZ-Grenzen für den Variationskoeffizienten
    xyz_grenze_x: float = 0.5   # VK < 0,5 -> X
    xyz_grenze_y: float = 1.0   # VK < 1,0 -> Y, sonst Z


@dataclass
class Material:
    """Materialstamm- und Bewegungsdaten eines Artikels."""

    nummer: str
    bezeichnung: str = ""
    wert: float = 0.0                         # Preis je Einheit [EUR/Stück]
    jahresbedarf: float | None = None         # D [Stück/Jahr]
    bestellkosten: float | None = None        # Kb [EUR/Bestellung]
    lagerhaltungskosten: float | None = None  # H [EUR/(Stück*Jahr)]
    lieferzeit_wochen: float | None = None    # Wiederbeschaffungszeit [Wochen]
    sicherheitsbestand: float = 0.0           # SB [Stück]
    lagerbestand: float = 0.0                 # aktueller Lagerbestand [Stück]
    offene_bestellungen: float = 0.0          # bereits bestellt, noch nicht geliefert [Stück]
    verbrauchsreihe: list[float] = field(default_factory=list)  # z. B. 12 Monatswerte
    verfahren_vorgabe: str | None = None      # manuelle Überschreibung des Bestellverfahrens
    begruendung: str | None = None            # Pflicht bei verfahren_vorgabe


@dataclass
class AbcZeile:
    nummer: str
    wert: float
    verbrauch: float
    verbrauchswert: float
    anteil: float
    anteil_kumuliert: float
    klasse: str


@dataclass
class XyzZeile:
    nummer: str
    mittelwert: float
    standardabweichung: float
    variationskoeffizient: float
    klasse: str


@dataclass
class Ergebnis:
    """Ergebnis aller Module für ein Material."""

    nummer: str
    bezeichnung: str
    gueltig: bool = True
    hinweise: list[str] = field(default_factory=list)
    abc: str | None = None
    xyz: str | None = None
    strategie: str | None = None
    verfahren: str | None = None
    tagesbedarf: float | None = None
    meldebestand: float | None = None
    losgroesse_roh: float | None = None
    losgroesse: int | None = None
    kennzahlen: dict[str, float] = field(default_factory=dict)
    bestellvorschlag: float | None = None
    status: str = ""
