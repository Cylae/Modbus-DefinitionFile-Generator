import unittest
import os
import json
from pdfminer.pdfparser import PDFSyntaxError
from unittest.mock import patch, MagicMock
from parser import (
    parse_modbus_text, generate_csv_data, ParserError,
    _is_header_row, _parse_row_with_map, ModbusRegister, _is_stop_header
)


class TestParserUnit(unittest.TestCase):
    """Unit tests for individual functions in the parser."""

    def test_is_header_row(self):
        """Tests the _is_header_row function with various valid and invalid inputs."""
        # A perfect, expected header
        valid_header = ["No.", "Signal Name", "Address", "Number of Registers", "R/W Access", "Data Type", "Unit"]
        expected_map = {
            'index': 0, 'name': 1, 'address': 2, 'num_reg': 3, 'access': 4, 'type': 5, 'unit': 6
        }
        self.assertEqual(_is_header_row(valid_header, " ".join(valid_header).lower()), expected_map)

        # A header with fewer columns, but still valid
        partial_header = ["Address", "Name", "Type", "Unit"]
        expected_map_partial = {'address': 0, 'name': 1, 'type': 2, 'unit': 3}
        self.assertEqual(_is_header_row(partial_header, " ".join(partial_header).lower()), expected_map_partial)

        # A header with keywords in different languages/abbreviations
        mixed_header = ["Index", "Nom du Signal", "Addresse", "Typ", "Un."]
        expected_map_mixed = {'index': 0, 'name': 1, 'address': 2, 'type': 3, 'unit': 4}
        self.assertEqual(_is_header_row(mixed_header, " ".join(mixed_header).lower()), expected_map_mixed)

        # A header with the new alternative keywords
        alternative_header = ["#", "Description", "Register", "Scaling", "Read/Write", "Format", "Units"]
        expected_map_alternative = {
            'index': 0, 'name': 1, 'address': 2, 'gain': 3, 'access': 4, 'type': 5, 'unit': 6
        }
        self.assertEqual(_is_header_row(alternative_header, " ".join(alternative_header).lower()), expected_map_alternative)

        # A row that is clearly not a header (data row)
        data_row = ["1", "Inverter Status", "40001", "1", "RO", "UINT16", ""]
        self.assertIsNone(_is_header_row(data_row, " ".join(data_row).lower()))

        # An empty row
        self.assertIsNone(_is_header_row([], ""))

    def test_parse_row_with_map(self):
        """Tests the _parse_row_with_map function."""
        column_map = {
            'index': 0, 'name': 1, 'address': 2, 'num_reg': 3, 'access': 4,
            'type': 5, 'unit': 6, 'gain': 7, 'scope': 8
        }
        valid_row = ["10", "Inverter Power", "40001", "2", "RO", "INT32", "W", "10", "Active power"]
        register = _parse_row_with_map(valid_row, column_map)
        self.assertIsInstance(register, ModbusRegister)
        self.assertEqual(register.name, "Inverter Power")
        self.assertAlmostEqual(register.gain, 0.1)

        # Test with a row that has a non-numeric index (should be invalid)
        invalid_index_row = ["N/A", "Inverter Temp", "40011", "1", "RO", "INT16", "C", "1", ""]
        self.assertIsNone(_parse_row_with_map(invalid_index_row, column_map))

        # Test automatic num_reg adjustment for 32-bit types
        row_32bit = ["14", "Total Energy", "40100", "1", "RO", "UINT32", "kWh", "1", ""]
        register_32bit = _parse_row_with_map(row_32bit, column_map)
        self.assertIsNotNone(register_32bit)
        self.assertEqual(register_32bit.num_reg, 2, "num_reg should be corrected to 2 for UINT32")

    def test_is_stop_header(self):
        """Tests the _is_stop_header function."""
        self.assertTrue(_is_stop_header(["4.1", "Alarm and Event Definitions"]))
        self.assertTrue(_is_stop_header(["5.", "Error Code List"]))
        self.assertFalse(_is_stop_header(["3.5", "Register Definitions"]))
        self.assertFalse(_is_stop_header(["10", "Inverter Power", "40001", "2", "RO"]))
        self.assertFalse(_is_stop_header([]))

    @patch('parser.pdfplumber.open')
    def test_scope_continuation_logic(self, mock_pdfplumber_open):
        """Tests that the parser correctly handles multi-line scope/description fields."""
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_table = [
            ["No.", "Signal Name", "Address", "Scope"],
            ["15", "Device Status", "40100", "Provides detailed status"],
            ["of the device, including", None, None, None],
            ["operational mode.", None, None, None],
            ["16", "Next Register", "40101", "Another register"]
        ]
        mock_page.extract_tables.return_value = [mock_table]
        mock_pdf.pages = [mock_page]
        mock_pdfplumber_open.return_value.__enter__.return_value = mock_pdf

        registers = parse_modbus_text("dummy/file.pdf")
        self.assertEqual(len(registers), 2)
        expected_scope = "Provides detailed status of the device, including operational mode."
        self.assertEqual(registers[0].scope, expected_scope)
        self.assertEqual(registers[1].scope, "Another register")

    def test_error_handling(self):
        """Tests that the parser raises appropriate errors."""
        # Test for a file where no valid header is ever found
        with patch('parser.pdfplumber.open') as mock_pdfplumber_open:
            mock_pdf = MagicMock()
            mock_page = MagicMock()
            mock_table = [["Col A", "Col B", "Col C"], ["1", "2", "3"]] # A table with no valid header
            mock_page.extract_tables.return_value = [mock_table]
            mock_pdf.pages = [mock_page]
            mock_pdfplumber_open.return_value.__enter__.return_value = mock_pdf

            with self.assertRaisesRegex(ParserError, "Aucun en-tête de tableau Modbus valide"):
                parse_modbus_text("dummy/file.pdf")

        # Test for a corrupted PDF file
        with patch('parser.pdfplumber.open') as mock_pdfplumber_open:
            # Simulate the error that pdfminer would raise
            mock_pdfplumber_open.side_effect = PDFSyntaxError("Corrupted file")

            with self.assertRaisesRegex(ParserError, "Erreur de syntaxe PDF"):
                parse_modbus_text("dummy/corrupted.pdf")


class TestParserEndToEnd(unittest.TestCase):
    """
    Data-driven end-to-end tests. It scans the `test_data` directory
    for PDF files and compares their parsing results against corresponding
    '.json' golden files.
    """
    def test_parsing_from_test_data(self):
        test_data_dir = "test_data"
        test_files = [f for f in os.listdir(test_data_dir) if f.endswith('.pdf')]

        self.assertGreater(len(test_files), 0, "No test files found in test_data directory.")

        for pdf_file in test_files:
            base_name = os.path.splitext(pdf_file)[0]
            pdf_path = os.path.join(test_data_dir, pdf_file)
            json_path = os.path.join(test_data_dir, f"{base_name}.json")

            with self.subTest(pdf_file=pdf_file):
                self.assertTrue(os.path.exists(json_path), f"Golden file not found for {pdf_file}")

                # Parse the actual PDF
                parsed_registers = parse_modbus_text(pdf_path)
                self.assertIsNotNone(parsed_registers)
                self.assertIsInstance(parsed_registers, list)

                # Load the expected results from the golden file
                with open(json_path, 'r') as f:
                    expected_data = json.load(f)

                # Create a dictionary of parsed registers by name for easy lookup
                parsed_map = {reg.name: reg for reg in parsed_registers}

                # Compare the parsed data against the expected data
                for expected_reg in expected_data:
                    reg_name = expected_reg["name"]
                    self.assertIn(reg_name, parsed_map, f"Register '{reg_name}' not found in parsed output for {pdf_file}")

                    actual_reg = parsed_map[reg_name]
                    for key, expected_value in expected_reg.items():
                        actual_value = getattr(actual_reg, key)
                        self.assertEqual(actual_value, expected_value,
                                         f"Mismatch for register '{reg_name}', key '{key}' in {pdf_file}")

if __name__ == '__main__':
    unittest.main()
