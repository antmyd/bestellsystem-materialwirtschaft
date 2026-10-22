"""Hauptablauf: führt die Module M1 bis M9 für alle Materialien aus."""

from __future__ import annotations

from dataclasses import dataclass, field

from . import bestellverfahren as bv
from .analyse import abc_analyse, xyz_analyse
from .bedarf import Stueckliste, StuecklistenFehler, mengenstueckliste, verbrauchsgebundener_bedarf
from .berechnung import (andler_losgroesse, aufrunden, bestellpruefung, kennzahlen,
                         lieferzeit_in_tagen, meldebestand, tagesbedarf,
                         zykluszeit_bestellmenge)
from .modelle import AbcZeile, Ergebnis, Material, Parameter, XyzZeile
from .protokoll import Protokoll, zahl


@dataclass
class Lauf:
    """Alles, was ein Programmlauf erzeugt (Eingabe für M10 Ausgabe)."""

    parameter: Parameter
    ergebnisse: list[Ergebnis] = field(default_factory=list)
    abc: list[AbcZeile] = field(default_factory=list)
    xyz: list[XyzZeile] = field(default_factory=list)
    mengenstuecklisten: dict[str, dict[str, float]] = field(default_factory=dict)
    protokoll: Protokoll = field(default_factory=Protokoll)


# ---------------------------------------------------------------- M1
def validiere(material: Material, bekannte_nummern: set[str]) -> list[str]:
    """Prüfregeln aus dem Datenmodell. Liefert die Liste der Fehler."""
    fehler = []
    if not material.nummer:
        fehler.append("Artikelnummer fehlt")
    elif material.nummer in bekannte_nummern:
        fehler.append(f"Artikelnummer {material.nummer} ist doppelt")
    if material.wert <= 0:
        fehler.append("Wert muss größer als 0 sein")
    for name in ("jahresbedarf", "bestellkosten", "lagerhaltungskosten", "lieferzeit_wochen"):
        wert = getattr(material, name)
        if wert is not None and wert <= 0:
            fehler.append(f"{name} muss größer als 0 sein")
    for name in ("sicherheitsbestand", "lagerbestand", "offene_bestellungen"):
        if getattr(material, name) < 0:
            fehler.append(f"{name} darf nicht negativ sein")
    if any(v < 0 for v in material.verbrauchsreihe):
        fehler.append("Verbrauchsreihe enthält negative Werte")
    if material.verfahren_vorgabe:
        if material.verfahren_vorgabe not in bv.VERFAHREN:
            fehler.append(f"unbekanntes Bestellverfahren: {material.verfahren_vorgabe}")
        if not material.begruendung:
            fehler.append("manuelle Vorgabe des Bestellverfahrens ohne Begründung")
    return fehler


# ---------------------------------------------------------------- Ablauf
def fuehre_aus(materialien: list[Material],
               parameter: Parameter = Parameter(),
               stueckliste: Stueckliste | None = None,
               primaerbedarf: dict[str, float] | None = None) -> Lauf:
    lauf = Lauf(parameter)
    p = lauf.protokoll

    # M1 Datenerfassung und Validierung
    gueltig: list[Material] = []
    bekannte: set[str] = set()
    ergebnisse: dict[str, Ergebnis] = {}
    for m in materialien:
        ergebnis = Ergebnis(m.nummer, m.bezeichnung)
        fehler = validiere(m, bekannte)
        bekannte.add(m.nummer)
        if fehler:
            ergebnis.gueltig = False
            ergebnis.hinweise.extend(fehler)
            ergebnis.status = "ungültig – übersprungen"
            for f in fehler:
                p.schreibe("M1", m.nummer, "Prüfung", "", "", f"Fehler: {f}")
        else:
            gueltig.append(m)
        lauf.ergebnisse.append(ergebnis)
        ergebnisse.setdefault(m.nummer, ergebnis)

    # M2 Bedarfsermittlung
    sekundaerbedarf: dict[str, float] = {}
    if stueckliste and primaerbedarf:
        for erzeugnis, menge in primaerbedarf.items():
            try:
                liste = mengenstueckliste(stueckliste, erzeugnis, 1.0)
            except StuecklistenFehler as fehler:
                p.schreibe("M2", erzeugnis, "Stücklistenauflösung", "", "", f"Abbruch: {fehler}")
                continue
            lauf.mengenstuecklisten[erzeugnis] = liste
            for teil, je_stueck in liste.items():
                zusatz = je_stueck * menge
                sekundaerbedarf[teil] = sekundaerbedarf.get(teil, 0.0) + zusatz
                p.schreibe("M2", teil, f"Bedarf aus Primärbedarf {erzeugnis}",
                           "Primärbedarf × Menge aus Mengenstückliste",
                           f"{zahl(menge)} × {zahl(je_stueck)}", f"{zahl(zusatz)} Stück/Jahr")

    mit_bedarf: list[Material] = []
    for m in gueltig:
        e = ergebnisse[m.nummer]
        if m.jahresbedarf is not None:
            p.schreibe("M2", m.nummer, "Jahresbedarf", "Eingabe", "", f"{zahl(m.jahresbedarf)} Stück")
        elif m.nummer in sekundaerbedarf:
            m.jahresbedarf = sekundaerbedarf[m.nummer]
            p.schreibe("M2", m.nummer, "Jahresbedarf", "programmgebunden (Stückliste)", "",
                       f"{zahl(m.jahresbedarf)} Stück")
        elif m.verbrauchsreihe:
            m.jahresbedarf = verbrauchsgebundener_bedarf(m.verbrauchsreihe)
            p.schreibe("M2", m.nummer, "Jahresbedarf", "verbrauchsgebunden: Mittelwert × 12",
                       f"{zahl(m.jahresbedarf / 12)} × 12", f"{zahl(m.jahresbedarf)} Stück")
        else:
            e.gueltig = False
            e.hinweise.append("kein Jahresbedarf ermittelbar")
            e.status = "ungültig – kein Bedarf"
            continue
        mit_bedarf.append(m)

    # M3 ABC-Analyse über alle Materialien mit Bedarf
    lauf.abc = abc_analyse([(m.nummer, m.wert, m.jahresbedarf) for m in mit_bedarf], parameter, p)
    for zeile in lauf.abc:
        ergebnisse[zeile.nummer].abc = zeile.klasse

    for m in mit_bedarf:
        e = ergebnisse[m.nummer]

        # M4 XYZ-Analyse
        if len(m.verbrauchsreihe) >= 2:
            try:
                zeile = xyz_analyse(m.nummer, m.verbrauchsreihe, parameter, p)
                lauf.xyz.append(zeile)
                e.xyz = zeile.klasse
            except ValueError as fehler:
                e.hinweise.append(str(fehler))
        else:
            e.hinweise.append("keine Verbrauchsreihe: XYZ-Klasse unbekannt")

        # M5 Bestellverfahren
        if e.xyz:
            e.strategie = bv.strategie(e.abc, e.xyz)
            e.verfahren = bv.waehle_verfahren(e.abc, e.xyz)
        else:
            e.verfahren = bv.MELDEBESTAND
            e.hinweise.append("Annahme konstanter Verbrauch -> Meldebestandsverfahren")
        if m.verfahren_vorgabe:
            p.schreibe("M5", m.nummer, "Bestellverfahren", "manuelle Vorgabe",
                       f"Vorschlag wäre {e.verfahren}", f"{m.verfahren_vorgabe} ({m.begruendung})")
            e.hinweise.append(f"Verfahren manuell überschrieben: {m.begruendung}")
            e.verfahren = m.verfahren_vorgabe
        else:
            p.schreibe("M5", m.nummer, "Bestellverfahren", "ABC-XYZ-Matrix",
                       f"{e.abc}{e.xyz or '?'}", e.verfahren)
        moment = bv.AUSLOESENDES_MOMENT[e.verfahren]

        if e.verfahren not in bv.MIT_LOSGROESSE:
            e.status = f"{e.verfahren} (auslösendes Moment: {moment}) – keine Losgrößenrechnung"
            continue

        fehlend = [n for n in ("bestellkosten", "lagerhaltungskosten", "lieferzeit_wochen")
                   if getattr(m, n) is None]
        if fehlend:
            e.hinweise.append("für Meldebestand/Losgröße fehlt: " + ", ".join(fehlend))
            e.status = f"{e.verfahren} – Daten unvollständig"
            continue

        # M6 Meldebestand
        e.tagesbedarf = tagesbedarf(m.jahresbedarf, parameter.arbeitstage_pro_jahr)
        lz_tage = lieferzeit_in_tagen(m.lieferzeit_wochen, parameter.arbeitstage_pro_woche)
        e.meldebestand = meldebestand(e.tagesbedarf, lz_tage, m.sicherheitsbestand)
        p.schreibe("M6", m.nummer, "Tagesbedarf", "Jahresbedarf / Arbeitstage",
                   f"{zahl(m.jahresbedarf)} / {parameter.arbeitstage_pro_jahr}",
                   f"{zahl(e.tagesbedarf)} Stück/Tag")
        p.schreibe("M6", m.nummer, "Lieferzeit in Tagen", "Wochen × Arbeitstage pro Woche",
                   f"{zahl(m.lieferzeit_wochen)} × {parameter.arbeitstage_pro_woche}",
                   f"{zahl(lz_tage)} Tage")
        p.schreibe("M6", m.nummer, "Meldebestand",
                   "Tagesbedarf × Lieferzeit in Tagen + Sicherheitsbestand",
                   f"{zahl(e.tagesbedarf)} × {zahl(lz_tage)} + {zahl(m.sicherheitsbestand)}",
                   f"{zahl(e.meldebestand)} Stück")

        # M7 Losgröße nach Andler
        e.losgroesse_roh = andler_losgroesse(m.bestellkosten, m.jahresbedarf, m.lagerhaltungskosten)
        e.losgroesse = aufrunden(e.losgroesse_roh)
        p.schreibe("M7", m.nummer, "Optimale Bestellmenge Q", "Wurzel(2 × Kb × D / H)",
                   f"Wurzel(2 × {zahl(m.bestellkosten)} × {zahl(m.jahresbedarf)} / "
                   f"{zahl(m.lagerhaltungskosten)}) = {zahl(e.losgroesse_roh)}",
                   f"{e.losgroesse} Stück (aufgerundet)")

        # M8 Kennzahlen
        k = kennzahlen(m.jahresbedarf, e.losgroesse, m.bestellkosten, m.lagerhaltungskosten,
                       m.sicherheitsbestand, m.wert, parameter.arbeitstage_pro_jahr, m.lagerbestand)
        e.kennzahlen = k.als_dict()
        p.schreibe("M8", m.nummer, "Bestellhäufigkeit", "D / Q",
                   f"{zahl(m.jahresbedarf)} / {e.losgroesse}", f"{zahl(k.bestellhaeufigkeit)} pro Jahr")
        p.schreibe("M8", m.nummer, "Bestellzyklus", "Arbeitstage / Bestellhäufigkeit",
                   f"{parameter.arbeitstage_pro_jahr} / {zahl(k.bestellhaeufigkeit)}",
                   f"{zahl(k.bestellzyklus_tage)} Tage")
        p.schreibe("M8", m.nummer, "Durchschnittlicher Bestand", "Q / 2 + Sicherheitsbestand",
                   f"{e.losgroesse} / 2 + {zahl(m.sicherheitsbestand)}",
                   f"{zahl(k.durchschnittlicher_bestand)} Stück")
        p.schreibe("M8", m.nummer, "Bestellkosten pro Jahr", "D / Q × Kb",
                   f"{zahl(k.bestellhaeufigkeit)} × {zahl(m.bestellkosten)}",
                   f"{zahl(k.bestellkosten_jahr)} EUR")
        p.schreibe("M8", m.nummer, "Lagerhaltungskosten pro Jahr", "(Q / 2 + SB) × H",
                   f"{zahl(k.durchschnittlicher_bestand)} × {zahl(m.lagerhaltungskosten)}",
                   f"{zahl(k.lagerkosten_jahr)} EUR "
                   f"(davon Sicherheitsbestand {zahl(k.lagerkosten_sicherheitsbestand)} EUR)")
        p.schreibe("M8", m.nummer, "Gesamtkosten pro Jahr", "Bestellkosten + Lagerhaltungskosten",
                   f"{zahl(k.bestellkosten_jahr)} + {zahl(k.lagerkosten_jahr)}",
                   f"{zahl(k.gesamtkosten_jahr)} EUR")
        p.schreibe("M8", m.nummer, "Reichweite", "Lagerbestand / Tagesbedarf",
                   f"{zahl(m.lagerbestand)} / {zahl(e.tagesbedarf)}",
                   f"{zahl(k.reichweite_tage)} Tage")

        # M9 Bestellprüfung
        if e.verfahren == bv.MELDEBESTAND:
            pr = bestellpruefung(m.lagerbestand, m.offene_bestellungen,
                                 e.meldebestand, e.losgroesse, e.tagesbedarf)
            p.schreibe("M9", m.nummer, "Bestellprüfung",
                       "disponibler Bestand <= Meldebestand?",
                       f"{zahl(pr.disponibler_bestand)} <= {zahl(e.meldebestand)}",
                       pr.text)
            e.bestellvorschlag = pr.menge if pr.bestellen else None
            e.status = pr.text
        else:  # Zykluszeitverfahren
            hoechst, menge = zykluszeit_bestellmenge(
                e.tagesbedarf, k.bestellzyklus_tage, lz_tage, m.sicherheitsbestand,
                m.lagerbestand, m.offene_bestellungen)
            p.schreibe("M9", m.nummer, "Bestellmenge zum Bestelltermin",
                       "Höchstbestand − disponibler Bestand",
                       f"{zahl(hoechst)} − {zahl(m.lagerbestand + m.offene_bestellungen)}",
                       f"{menge} Stück, nächster Termin alle {zahl(k.bestellzyklus_tage)} Tage")
            e.bestellvorschlag = menge if menge > 0 else None
            e.status = (f"zum nächsten Bestelltermin {menge} Stück bestellen "
                        f"(Zyklus {zahl(k.bestellzyklus_tage)} Tage)")

    return lauf
