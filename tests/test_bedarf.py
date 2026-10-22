"""Übung 5 Stücklisten (Material X) als Abnahmetest für M2."""

import unittest

from bestellsystem.bedarf import (StuecklistenFehler, baukastenstueckliste, dispositionsstufen,
                                  mengenstueckliste, verbrauchsgebundener_bedarf)

STUECKLISTE_X = {
    "Material X": {"Bauteil A": 2, "Teil c": 5, "Bauteil B": 3},
    "Bauteil A": {"Bauteil B": 1, "Teil c": 2},
    "Bauteil B": {"Teil a": 5, "Teil b": 3},
}


class TestStueckliste(unittest.TestCase):
    def test_mengenstueckliste_wie_musterloesung(self):
        self.assertEqual(
            mengenstueckliste(STUECKLISTE_X, "Material X"),
            {"Bauteil A": 2, "Bauteil B": 5, "Teil c": 9, "Teil a": 25, "Teil b": 15})

    def test_mengenstueckliste_skaliert_mit_primaerbedarf(self):
        liste = mengenstueckliste(STUECKLISTE_X, "Material X", 100)
        self.assertEqual(liste["Teil a"], 2500)

    def test_baukastenstuecklisten_wie_musterloesung(self):
        self.assertEqual(baukastenstueckliste(STUECKLISTE_X, "Material X"),
                         {"Bauteil A": 2, "Bauteil B": 3, "Teil c": 5})
        self.assertEqual(baukastenstueckliste(STUECKLISTE_X, "Bauteil A"),
                         {"Bauteil B": 1, "Teil c": 2})
        self.assertEqual(baukastenstueckliste(STUECKLISTE_X, "Bauteil B"),
                         {"Teil a": 5, "Teil b": 3})

    def test_dispositionsstufen_mehrfachteile_auf_unterste_stufe(self):
        self.assertEqual(dispositionsstufen(STUECKLISTE_X, "Material X"), {
            "Material X": 0, "Bauteil A": 1, "Bauteil B": 2,
            "Teil c": 2, "Teil a": 3, "Teil b": 3})

    def test_zyklus_wird_erkannt(self):
        with self.assertRaises(StuecklistenFehler):
            dispositionsstufen({"A": {"B": 1}, "B": {"A": 1}}, "A")


class TestVerbrauchsgebunden(unittest.TestCase):
    def test_mittelwert_hochgerechnet(self):
        self.assertEqual(verbrauchsgebundener_bedarf([900, 1000, 1100] * 4), 12000)

    def test_leere_reihe(self):
        with self.assertRaises(ValueError):
            verbrauchsgebundener_bedarf([])


if __name__ == "__main__":
    unittest.main()
