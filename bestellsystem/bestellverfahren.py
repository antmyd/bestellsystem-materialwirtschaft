"""M5 Bestellverfahren wählen.

Schritt 1: Beschaffungsstrategie aus der ABC-XYZ-Matrix (Folie "ABC – XYZ Analyse").
Schritt 2: Bestellverfahren und sein auslösendes Moment.

    Bereitstellverfahren   -> auslösendes Moment: Verbrauch
    Meldebestandsverfahren -> auslösendes Moment: Bestand
    Zykluszeitverfahren    -> auslösendes Moment: Zeitpunkt
"""

from __future__ import annotations

BEREITSTELL = "Bereitstellverfahren"
MELDEBESTAND = "Meldebestandsverfahren"
ZYKLUSZEIT = "Zykluszeitverfahren"
NACH_BEDARF = "Bestellung nach Bedarf"
EINZELBESTELLUNG = "Einmalige Bestellung, wenn notwendig"

AUSLOESENDES_MOMENT = {
    BEREITSTELL: "Verbrauch",
    MELDEBESTAND: "Bestand",
    ZYKLUSZEIT: "Zeitpunkt",
    NACH_BEDARF: "konkreter Bedarf",
    EINZELBESTELLUNG: "konkreter Bedarf",
}

VERFAHREN = tuple(AUSLOESENDES_MOMENT)

# Verfahren, für die Meldebestand und Losgröße gebraucht werden
MIT_LOSGROESSE = (MELDEBESTAND, ZYKLUSZEIT)


def strategie(abc: str, xyz: str) -> str:
    """Beschaffungsstrategie laut ABC-XYZ-Matrix."""
    if xyz in ("X", "Y"):
        if abc == "A":
            return "gut planbar: Just in Time oder Just in Sequence"
        return "gut planbar: Bestellung nach Verbrauch"
    if abc == "A":
        return "schwer planbar: Bestellung nach Bedarf"
    return "keine Planung nötig: einmalige Bestellung, wenn notwendig"


def waehle_verfahren(abc: str, xyz: str) -> str:
    """Standardvorschlag für das Bestellverfahren.

    - A + X/Y (JIT/JIS): Bereitstellverfahren, Nachschub nach tatsächlichem
      Verbrauch (Pull-Prinzip, z. B. Kanban), wenig Kapitalbindung.
    - B/C + X/Y (Bestellung nach Verbrauch): Meldebestandsverfahren mit
      Andler-Losgröße; einfach und vorhersehbar.
    - A + Z: Bestellung nach Bedarf.
    - B/C + Z: einmalige Bestellung, wenn notwendig.
    """
    if xyz in ("X", "Y"):
        return BEREITSTELL if abc == "A" else MELDEBESTAND
    return NACH_BEDARF if abc == "A" else EINZELBESTELLUNG
