import unittest
import os
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
    """End-to-end tests for the Modbus definition parser."""

    def test_huawei_sun2000_pdf_parsing(self):
        """Tests the full pipeline on the Huawei SUN2000 PDF."""
        filepath = "Definition/09. SUN2000-12~25K-MB0 Modbus Interface Definitions (2).pdf"
        self.assertTrue(os.path.exists(filepath), f"Test file not found: {filepath}")
        header_info = {"protocol": "modbusRTU", "category": "Inverter", "manufacturer": "HUAWEI", "model": "SUN2000-25K-MB0", "write_code": "0"}

        registers = parse_modbus_text(filepath)
        self.assertIsNotNone(registers)
        self.assertGreater(len(registers), 300)

        csv_output = generate_csv_data(registers, header_info)
        self.assertIn("modbusRTU;Inverter;HUAWEI;SUN2000-25K-MB0;0", csv_output)
        self.assertIn("Model;Model", csv_output)

if __name__ == '__main__':
    unittest.main()
