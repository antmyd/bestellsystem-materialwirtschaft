"""Übung Beschaffung (Teil 2 und 3) als Abnahmetest für M6 bis M9."""

import unittest

from bestellsystem import bestellverfahren as bv
from bestellsystem.berechnung import (andler_losgroesse, aufrunden, bestellpruefung, kennzahlen,
                                      lieferzeit_in_tagen, meldebestand, tagesbedarf,
                                      zykluszeit_bestellmenge)

# Jährlicher Bedarf 12.000, Bestellkosten 100 EUR, Lagerhaltungskosten 5 EUR,
# Lieferzeit 2 Wochen, 240 Arbeitstage, Sicherheitsbestand 200
D, KB, H, SB = 12000, 100, 5, 200


class TestBeschaffung(unittest.TestCase):
    def test_tagesbedarf(self):
        self.assertEqual(tagesbedarf(D, 240), 50)

    def test_meldebestand_700(self):
        td = tagesbedarf(D, 240)
        self.assertEqual(meldebestand(td, lieferzeit_in_tagen(2, 5), SB), 700)

    def test_andler_692_82(self):
        q = andler_losgroesse(KB, D, H)
        self.assertAlmostEqual(q, 692.82, places=2)
        self.assertEqual(aufrunden(q), 693)

    def test_aufrunden_ganzer_zahl_bleibt(self):
        self.assertEqual(aufrunden(700.0), 700)

    def test_kennzahlen(self):
        k = kennzahlen(D, 693, KB, H, SB, wert=37.85, arbeitstage_pro_jahr=240, lagerbestand=700)
        self.assertAlmostEqual(k.bestellhaeufigkeit, 17.316, places=3)
        self.assertAlmostEqual(k.durchschnittlicher_bestand, 546.5)
        self.assertAlmostEqual(k.bestellkosten_jahr, 1731.60, places=2)
        self.assertAlmostEqual(k.lagerkosten_jahr, 2732.50, places=2)
        self.assertAlmostEqual(k.lagerkosten_sicherheitsbestand, 1000)
        self.assertAlmostEqual(k.reichweite_tage, 14)

    def test_im_optimum_sind_bestell_und_lagerkosten_gleich(self):
        q = andler_losgroesse(KB, D, H)
        k = kennzahlen(D, q, KB, H, 0, 1, 240, 0)
        self.assertAlmostEqual(k.bestellkosten_jahr, k.lagerkosten_jahr)

    def test_ungueltige_eingaben(self):
        with self.assertRaises(ValueError):
            andler_losgroesse(0, D, H)
        with self.assertRaises(ValueError):
            tagesbedarf(D, 0)


class TestBestellpruefung(unittest.TestCase):
    def test_bestellen_bei_meldebestand(self):
        pr = bestellpruefung(700, 0, 700, 693, 50)
        self.assertTrue(pr.bestellen)
        self.assertEqual(pr.menge, 693)

    def test_offene_bestellungen_zaehlen_mit(self):
        pr = bestellpruefung(600, 693, 700, 693, 50)
        self.assertFalse(pr.bestellen)
        self.assertAlmostEqual(pr.tage_bis_meldebestand, 593 / 50)

    def test_zykluszeit(self):
        hoechst, menge = zykluszeit_bestellmenge(50, 14, 10, 200, 500, 0)
        self.assertEqual(hoechst, 50 * 24 + 200)
        self.assertEqual(menge, 900)


class TestBestellverfahren(unittest.TestCase):
    def test_auslosende_momente(self):
        self.assertEqual(bv.AUSLOESENDES_MOMENT[bv.BEREITSTELL], "Verbrauch")
        self.assertEqual(bv.AUSLOESENDES_MOMENT[bv.MELDEBESTAND], "Bestand")
        self.assertEqual(bv.AUSLOESENDES_MOMENT[bv.ZYKLUSZEIT], "Zeitpunkt")

    def test_matrix(self):
        self.assertIn("Just in Time", bv.strategie("A", "X"))
        self.assertIn("nach Verbrauch", bv.strategie("C", "Y"))
        self.assertIn("nach Bedarf", bv.strategie("A", "Z"))
        self.assertIn("einmalige Bestellung", bv.strategie("B", "Z"))

    def test_verfahren(self):
        self.assertEqual(bv.waehle_verfahren("A", "X"), bv.BEREITSTELL)
        self.assertEqual(bv.waehle_verfahren("B", "Y"), bv.MELDEBESTAND)
        self.assertEqual(bv.waehle_verfahren("A", "Z"), bv.NACH_BEDARF)
        self.assertEqual(bv.waehle_verfahren("C", "Z"), bv.EINZELBESTELLUNG)


if __name__ == "__main__":
    unittest.main()
