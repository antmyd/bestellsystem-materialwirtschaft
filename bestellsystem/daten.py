"""Einlesen der Eingabedaten aus einer JSON-Datei."""

from __future__ import annotations

import json
from dataclasses import fields
from pathlib import Path

from .modelle import Material, Parameter


def lade(pfad: str | Path) -> dict:
    """Liest Parameter, Materialien, Stückliste und Primärbedarf.

    Aufbau der Datei: siehe daten/beispiel.json
    """
    with open(pfad, encoding="utf-8") as datei:
        roh = json.load(datei)

    erlaubt_parameter = {f.name for f in fields(Parameter)}
    erlaubt_material = {f.name for f in fields(Material)}

    unbekannt = set(roh.get("parameter", {})) - erlaubt_parameter
    if unbekannt:
        raise ValueError(f"unbekannte Parameter: {', '.join(sorted(unbekannt))}")
    parameter = Parameter(**roh.get("parameter", {}))

    materialien = []
    for eintrag in roh.get("materialien", []):
        unbekannt = set(eintrag) - erlaubt_material
        if unbekannt:
            raise ValueError(f"Material {eintrag.get('nummer')}: unbekannte Felder "
                             f"{', '.join(sorted(unbekannt))}")
        materialien.append(Material(**eintrag))

    return {
        "parameter": parameter,
        "materialien": materialien,
        "stueckliste": roh.get("stueckliste") or None,
        "primaerbedarf": roh.get("primaerbedarf") or None,
    }
