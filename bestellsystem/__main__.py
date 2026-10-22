"""Aufruf: python -m bestellsystem daten/beispiel.json [--ohne-protokoll]"""

from __future__ import annotations

import argparse
import sys

from .ablauf import fuehre_aus
from .ausgabe import bericht
from .daten import lade


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="bestellsystem",
        description="Bestellsystem für die Materialwirtschaft: Bedarf, ABC/XYZ, "
                    "Bestellverfahren, Meldebestand, Andler-Losgröße, Kennzahlen.")
    parser.add_argument("datei", help="JSON-Datei mit Parametern und Materialien")
    parser.add_argument("--ohne-protokoll", action="store_true",
                        help="Rechenprotokoll nicht ausgeben")
    args = parser.parse_args(argv)

    try:
        eingabe = lade(args.datei)
    except (OSError, ValueError, TypeError) as fehler:
        print(f"Fehler beim Einlesen: {fehler}", file=sys.stderr)
        return 1

    lauf = fuehre_aus(eingabe["materialien"], eingabe["parameter"],
                      eingabe["stueckliste"], eingabe["primaerbedarf"])
    print(bericht(lauf, mit_protokoll=not args.ohne_protokoll))
    return 0


if __name__ == "__main__":
    sys.exit(main())
