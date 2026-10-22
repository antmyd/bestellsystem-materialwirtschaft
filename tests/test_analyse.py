"""ABC- und XYZ-Analyse gegen die Musterlösungen aus der Übung."""

import unittest

from bestellsystem.analyse import abc_analyse, variationskoeffizient, xyz_analyse, xyz_klasse

ABC_DATEN = [
    ("1007", 136.20, 4000), ("1009", 37.85, 12000), ("1004", 17.50, 6000),
    ("1006", 6.25, 8000), ("1001", 3.25, 10000), ("1005", 1.60, 12400),
    ("1008", 2.10, 6800), ("1002", 1.10, 12800), ("1003", 1.75, 8000),
]


class TestAbc(unittest.TestCase):
    def setUp(self):
        self.ergebnis = abc_analyse(ABC_DATEN)

    def test_klassen_wie_musterloesung(self):
        klassen = {z.nummer: z.klasse for z in self.ergebnis}
        self.assertEqual(klassen, {
            "1007": "A", "1009": "A",
            "1004": "B", "1006": "B", "1001": "B",
            "1005": "C", "1008": "C", "1002": "C", "1003": "C"})

    def test_summe_und_sortierung(self):
        self.assertAlmostEqual(sum(z.verbrauchswert for z in self.ergebnis), 1_248_700)
        werte = [z.verbrauchswert for z in self.ergebnis]
        self.assertEqual(werte, sorted(werte, reverse=True))

    def test_kumulierte_anteile(self):
        kum = {z.nummer: round(z.anteil_kumuliert * 100, 2) for z in self.ergebnis}
        self.assertEqual(kum["1007"], 43.63)
        self.assertEqual(kum["1009"], 80.00)
        self.assertEqual(kum["1001"], 95.02)
        self.assertEqual(kum["1003"], 100.00)

    def test_grenzartikel_bleiben_in_oberer_klasse(self):
        zeile = next(z for z in self.ergebnis if z.nummer == "1009")
        self.assertGreater(zeile.anteil_kumuliert, 0.80)  # 80,003 %
        self.assertEqual(zeile.klasse, "A")


class TestXyz(unittest.TestCase):
    def test_aufgabe_datensaetze(self):
        for mittelwert, std, vk, klasse in [(50, 10, 0.2, "X"), (100, 20, 0.2, "X"),
                                            (30, 35, 1.167, "Z")]:
            berechnet = variationskoeffizient(mittelwert, std)
            self.assertAlmostEqual(berechnet, vk, places=3)
            self.assertEqual(xyz_klasse(berechnet), klasse)

    def test_klassengrenzen(self):
        self.assertEqual(xyz_klasse(0.49), "X")
        self.assertEqual(xyz_klasse(0.495), "X")   # liegt zwischen 0,49 und 0,5
        self.assertEqual(xyz_klasse(0.5), "Y")
        self.assertEqual(xyz_klasse(0.995), "Y")
        self.assertEqual(xyz_klasse(1.0), "Z")

    def test_mittelwert_null(self):
        with self.assertRaises(ValueError):
            variationskoeffizient(0, 5)

    def test_aus_verbrauchsreihe(self):
        zeile = xyz_analyse("t", [100, 100, 100, 100])
        self.assertEqual(zeile.variationskoeffizient, 0)
        self.assertEqual(zeile.klasse, "X")


if __name__ == "__main__":
    unittest.main()
