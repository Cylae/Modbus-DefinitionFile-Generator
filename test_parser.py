import unittest
import os
from parser import parse_modbus_text, generate_csv_data

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
