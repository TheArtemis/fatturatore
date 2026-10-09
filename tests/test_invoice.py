from __future__ import annotations

import json
import unittest
import xml.etree.ElementTree as ET
from contextlib import redirect_stdout
from datetime import date
from decimal import Decimal
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fatturatore.cli import (
    BANNER,
    format_eur,
    manage_progressives,
    parse_date,
    prompt_for_invoice_date,
    prompt_style,
    style,
    main,
)
from fatturatore.invoice import build_invoice_xml, calculate_amounts, parse_amount


class AmountParsingTests(unittest.TestCase):
    def test_accepts_italian_and_international_formats(self) -> None:
        examples = ("2917", "2917,00", "2.917,00", "2917.00", "2,917.00", "€ 2.917,00")
        for value in examples:
            with self.subTest(value=value):
                self.assertEqual(parse_amount(value), Decimal("2917.00"))

    def test_rejects_invalid_or_too_small_amounts(self) -> None:
        for value in ("", "abc", "1,2345", "-10", "0"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_amount(value)


class CalculationTests(unittest.TestCase):
    def test_reverse_calculates_sample_total(self) -> None:
        amounts = calculate_amounts(Decimal("2917.00"))
        self.assertEqual(amounts.gross, Decimal("2917.00"))
        self.assertEqual(amounts.total, Decimal("2919.00"))
        self.assertEqual(amounts.fee, Decimal("2804.81"))
        self.assertEqual(amounts.social_security, Decimal("112.19"))
        self.assertEqual(amounts.taxable_total, Decimal("2917.00"))
        self.assertEqual(amounts.rounding, Decimal("0.00"))

    def test_preserves_any_cent_total_with_at_most_one_cent_rounding(self) -> None:
        for cents in range(1, 1000):
            gross = Decimal(cents) / 100
            amounts = calculate_amounts(gross)
            reconstructed = (
                amounts.fee
                + amounts.social_security
                + amounts.rounding
            )
            self.assertEqual(reconstructed, gross)
            self.assertEqual(amounts.total, gross + Decimal("2.00"))
            self.assertLessEqual(abs(amounts.rounding), Decimal("0.01"))


class XmlGenerationTests(unittest.TestCase):
    def test_character_references_preserve_accented_reasons(self) -> None:
        reasons = (
            "Il compenso non è soggetto a ritenute d'acconto.",
            "Più attività: città, caffè & consulenza <annuale>.",
        )
        amounts = calculate_amounts(Decimal("1430.00"))
        with patch("fatturatore.invoice.REASONS", reasons):
            xml = build_invoice_xml(amounts, date(2026, 10, 8), "18", "00001")

        self.assertTrue(xml.isascii())
        self.assertIn(b"encoding='utf-8'", xml)
        self.assertIn(b"&#232;", xml)
        for source in (xml, xml.decode("latin-1")):
            with self.subTest(source_type=type(source).__name__):
                root = ET.fromstring(source)
                self.assertEqual(
                    tuple(element.text for element in root.findall(".//Causale")),
                    reasons,
                )

    def test_generates_expected_fatturapa_fields(self) -> None:
        amounts = calculate_amounts(Decimal("2917.00"))
        xml = build_invoice_xml(amounts, date(2026, 10, 7), "1", "00001")
        root = ET.fromstring(xml)
        self.assertEqual(root.attrib["versione"], "FPR12")
        self.assertIsNotNone(root.find("FatturaElettronicaHeader"))
        self.assertEqual(root.findtext(".//ProgressivoInvio"), "00001")
        self.assertEqual(root.findtext(".//RegimeFiscale"), "RF19")
        self.assertEqual(root.findtext(".//TipoCassa"), "TC22")
        self.assertEqual(root.findtext(".//Natura"), "N2.2")
        self.assertEqual(root.findtext(".//ImportoTotaleDocumento"), "2919.00")
        self.assertEqual(root.findtext(".//PrezzoTotale"), "2804.81")
        self.assertEqual(root.findtext(".//ImportoContributoCassa"), "112.19")
        self.assertEqual(root.findtext(".//ImportoBollo"), "2.00")
        recipient_code = root.findtext(".//CodiceDestinatario")
        assert recipient_code is not None
        self.assertEqual(len(recipient_code), 7)
        pec = root.findtext(".//PECDestinatario")
        assert pec is not None
        self.assertIn("@", pec)


class InteractiveCliTests(unittest.TestCase):
    def test_italian_currency_format(self) -> None:
        self.assertEqual(format_eur(Decimal("2919")), "2.919,00 EUR")

    def test_colour_can_be_enabled_or_disabled(self) -> None:
        with patch("fatturatore.cli.style.colours_enabled", return_value=True):
            self.assertIn("\033[", style("test", "\033[32m"))
        with patch("fatturatore.cli.style.colours_enabled", return_value=False):
            self.assertEqual(style("test", "\033[32m"), "test")

    def test_coloured_prompt_marks_non_printing_sequences_for_readline(self) -> None:
        with patch("fatturatore.cli.style.colours_enabled", return_value=True):
            prompt = prompt_style("Importo", "\033[32m")
        self.assertIn("\001\033[32m\002", prompt)
        self.assertIn("\001\033[0m\002", prompt)

    def test_date_parser_accepts_italian_and_iso_formats(self) -> None:
        expected = date(2026, 10, 8)
        self.assertEqual(parse_date("08/10/2026"), expected)
        self.assertEqual(parse_date("2026-10-08"), expected)

    def test_interactive_date_can_use_today_or_a_custom_date(self) -> None:
        today = date(2026, 10, 7)
        with patch("builtins.input", return_value=""):
            self.assertEqual(prompt_for_invoice_date(today), today)
        with patch("builtins.input", side_effect=["n", "08/10/2026"]):
            self.assertEqual(prompt_for_invoice_date(today), date(2026, 10, 8))

    def test_no_amount_shows_banner_and_prompts_for_gross(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "output"
            state = Path(temporary_directory) / "state.json"
            stdout = StringIO()
            with (
                patch("builtins.input", side_effect=["2.917,00", "s"]),
                patch("fatturatore.cli.main.DEFAULT_STATE_FILE", state),
                redirect_stdout(stdout),
            ):
                result = main(
                    [
                        "--numero",
                        "1",
                        "--data",
                        "2026-10-07",
                        "--output",
                        str(output),
                    ]
                )

            self.assertEqual(result, 0)
            self.assertIn(BANNER, stdout.getvalue())
            self.assertIn("RIEPILOGO FATTURA", stdout.getvalue())
            self.assertEqual(len(list(output.glob("*.xml"))), 1)

    def test_declining_confirmation_does_not_write_file_or_state(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "output"
            state = Path(temporary_directory) / "state.json"
            stdout = StringIO()
            with (
                patch("builtins.input", side_effect=["2917", "", "n"]),
                patch("fatturatore.cli.main.DEFAULT_STATE_FILE", state),
                redirect_stdout(stdout),
            ):
                result = main(["--output", str(output)])

            self.assertEqual(result, 0)
            self.assertIn("nessun file generato", stdout.getvalue())
            self.assertFalse(output.exists())
            self.assertFalse(state.exists())

    def test_progressive_manager_updates_invoice_numbers_and_preserves_transmission(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            state_path = Path(temporary_directory) / "state.json"
            state_path.write_text(
                json.dumps({"next_transmission": 42, "years": {"2026": 5, "2027": 3}}),
                encoding="utf-8",
            )
            stdout = StringIO()
            with (
                patch("builtins.input", side_effect=["1", "12", "2", "2027", "1", "8", "q"]),
                redirect_stdout(stdout),
            ):
                result = manage_progressives(state_path, initial_year=2026)

            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(result, 0)
            self.assertEqual(state["years"]["2026"], 12)
            self.assertEqual(state["years"]["2027"], 8)
            self.assertEqual(state["next_transmission"], 42)
            self.assertIn("Prossima fattura 2026 impostata a 12", stdout.getvalue())
            self.assertIn("Prossima fattura 2027 impostata a 8", stdout.getvalue())
            self.assertNotIn("Prossimo invio", stdout.getvalue())
            self.assertNotIn("SdI", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
