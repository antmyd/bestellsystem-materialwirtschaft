"""Gesamtablauf M1 bis M10 mit den Beispieldaten."""

import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from bestellsystem.__main__ import main
from bestellsystem.ablauf import fuehre_aus, validiere
from bestellsystem.daten import lade
from bestellsystem.modelle import Material

BEISPIEL = Path(__file__).resolve().parent.parent / "daten" / "beispiel.json"


class TestAblauf(unittest.TestCase):
    def setUp(self):
        eingabe = lade(BEISPIEL)
        self.lauf = fuehre_aus(eingabe["materialien"], eingabe["parameter"],
                               eingabe["stueckliste"], eingabe["primaerbedarf"])
        self.ergebnis = {e.nummer: e for e in self.lauf.ergebnisse}

    def test_uebung_beschaffung_1009(self):
        e = self.ergebnis["1009"]
        self.assertEqual(e.verfahren, "Meldebestandsverfahren")
        self.assertEqual(e.meldebestand, 700)
        self.assertEqual(e.losgroesse, 693)
        self.assertEqual(e.bestellvorschlag, 693)  # Lagerbestand 650 <= 700

    def test_manuelle_vorgabe_wird_protokolliert(self):
        eintraege = self.lauf.protokoll.fuer("1009")
        self.assertTrue(any("manuelle Vorgabe" in e.formel for e in eintraege))

    def test_unvollstaendige_daten_werden_gemeldet(self):
        e = self.ergebnis["1003"]
        self.assertIsNone(e.losgroesse)
        self.assertIn("Daten unvollständig", e.status)

    def test_stuecklistenaufloesung(self):
        self.assertEqual(self.lauf.mengenstuecklisten["Material X"]["Teil c"], 9)

    def test_jeder_schritt_im_protokoll(self):
        module = {e.modul for e in self.lauf.protokoll.eintraege}
        self.assertTrue({"M2", "M3", "M4", "M5", "M6", "M7", "M8", "M9"} <= module)

    def test_kommandozeile(self):
        ausgabe = io.StringIO()
        with redirect_stdout(ausgabe):
            code = main([str(BEISPIEL), "--ohne-protokoll"])
        self.assertEqual(code, 0)
        self.assertIn("Meldebestand erreicht: 693 Stück bestellen", ausgabe.getvalue())


class TestValidierung(unittest.TestCase):
    def test_fehler(self):
        m = Material("X1", wert=0, jahresbedarf=-5, verfahren_vorgabe="Zykluszeitverfahren")
        fehler = validiere(m, set())
        self.assertEqual(len(fehler), 3)

    def test_doppelte_nummer(self):
        self.assertTrue(validiere(Material("X1", wert=1), {"X1"}))

    def test_ungueltiges_material_wird_uebersprungen(self):
        lauf = fuehre_aus([Material("ok", wert=2, jahresbedarf=100),
                           Material("kaputt", wert=-1, jahresbedarf=100)])
        status = {e.nummer: e.gueltig for e in lauf.ergebnisse}
        self.assertEqual(status, {"ok": True, "kaputt": False})
        self.assertEqual([z.nummer for z in lauf.abc], ["ok"])


if __name__ == "__main__":
    unittest.main()
