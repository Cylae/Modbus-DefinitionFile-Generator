import unittest
import os
from parser import parse_modbus_text, generate_csv_data, _is_header_row


class TestParserUnit(unittest.TestCase):
    """Unit tests for individual functions in the parser."""

    def test_is_header_row(self):
        """Tests the _is_header_row function with various valid and invalid inputs."""
        # A perfect, expected header
        valid_header = ["No.", "Signal Name", "Address", "Number of Registers", "R/W Access", "Data Type", "Unit"]
        expected_map = {
            'index': 0,
            'name': 1,
            'address': 2,
            'num_reg': 3,
            'access': 4,
            'type': 5,
            'unit': 6
        }
        self.assertEqual(_is_header_row(valid_header, " ".join(valid_header).lower()), expected_map)

        # A header with fewer columns, but still valid
        partial_header = ["Address", "Name", "Type", "Unit"]
        expected_map_partial = {
            'address': 0,
            'name': 1,
            'type': 2,
            'unit': 3
        }
        self.assertEqual(_is_header_row(partial_header, " ".join(partial_header).lower()), expected_map_partial)

        # A header with keywords in different languages/abbreviations
        mixed_header = ["Index", "Nom du Signal", "Addresse", "Typ", "Un."]
        expected_map_mixed = {
            'index': 0,
            'name': 1,
            'address': 2,
            'type': 3,
            'unit': 4
        }
        self.assertEqual(_is_header_row(mixed_header, " ".join(mixed_header).lower()), expected_map_mixed)

        # A row that is clearly not a header (data row)
        data_row = ["1", "Inverter Status", "40001", "1", "RO", "UINT16", ""]
        self.assertIsNone(_is_header_row(data_row, " ".join(data_row).lower()))

        # A row with too few matching keywords to be a header
        not_a_header = ["Column 1", "Column 2", "Column 3", "Status"]
        self.assertIsNone(_is_header_row(not_a_header, " ".join(not_a_header).lower()))

        # An empty row
        empty_row = []
        self.assertIsNone(_is_header_row(empty_row, ""))

        # Test the 'gain' heuristic
        header_with_gain_in_type = ["Address", "Name", "Type/Gain", "Unit"]
        expected_map_gain = {
            'address': 0,
            'name': 1,
            'type': 2,
            'gain': 2, # Should map 'gain' to the same column as 'type'
            'unit': 3
        }
        self.assertEqual(_is_header_row(header_with_gain_in_type, " ".join(header_with_gain_in_type).lower()), expected_map_gain)


class TestParserEndToEnd(unittest.TestCase):
    """
    End-to-end tests for the Modbus definition parser.
    These tests process a sample PDF file and verify the generated CSV output.
    """

    def test_huawei_sun2000_pdf_parsing(self):
        """
        Tests the full pipeline on the Huawei SUN2000 PDF.
        It checks if registers are parsed and if the CSV is generated correctly.
        """
        filepath = "Definition/09. SUN2000-12~25K-MB0 Modbus Interface Definitions (2).pdf"
        self.assertTrue(os.path.exists(filepath), f"Test file not found: {filepath}")

        # Mock header info, as the GUI would provide it
        header_info = {
            "protocol": "modbusRTU",
            "category": "Inverter",
            "manufacturer": "HUAWEI",
            "model": "SUN2000-25K-MB0",
            "write_code": "0",
        }

        # 1. Test parsing
        registers = parse_modbus_text(filepath)
        self.assertIsNotNone(registers, "Parsing returned None")
        self.assertIsInstance(registers, list, "Parsing should return a list")
        self.assertGreater(len(registers), 0, "No registers were parsed from the PDF")

        # We know from previous runs that this file has a lot of registers.
        # Let's set a reasonable expectation.
        self.assertGreater(len(registers), 300, "Expected to parse at least 300 registers")


        # 2. Test CSV generation
        csv_output = generate_csv_data(registers, header_info)
        self.assertIsNotNone(csv_output, "CSV generation returned None")
        self.assertIsInstance(csv_output, str, "CSV output should be a string")
        self.assertIn("modbusRTU;Inverter;HUAWEI;SUN2000-25K-MB0;0", csv_output, "CSV header is missing or incorrect")
        self.assertIn("Model;Model", csv_output, "Expected 'Model' register in CSV output")

if __name__ == '__main__':
    unittest.main()
