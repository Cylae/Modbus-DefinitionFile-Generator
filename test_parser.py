"""
This script contains the end-to-end test for the Modbus definition parser.
It verifies that the parser can correctly process a sample PDF file and generate the expected CSV output.
"""

from parser import parse_modbus_text, generate_csv_data

# --- Final End-to-End Test Runner ---
def run_final_test(filepath):
    """
    Runs the full pipeline: parse PDF, generate CSV, and print the output.
    """
    print(f"--- Running Final End-to-End Test for: {filepath} ---")

    # Mock header info, as the GUI would provide it
    header_info = {
        "protocol": "modbusRTU",
        "category": "Inverter",
        "manufacturer": "HUAWEI",
        "model": "SUN2000-25K-MB0", # Using a model from the PDF
        "write_code": "0",
    }

    registers = parse_modbus_text(filepath)

    if registers:
        print(f"\n--- Successfully Parsed {len(registers)} Registers ---\n")
        csv_output = generate_csv_data(registers, header_info)
        print("--- Generated CSV Output ---")
        print(csv_output)
    else:
        print("--- Parsing Failed. No registers were returned. ---")

if __name__ == "__main__":
    # Run the final end-to-end test on one of the PDFs
    run_final_test("Definition/09. SUN2000-12~25K-MB0 Modbus Interface Definitions (2).pdf")
