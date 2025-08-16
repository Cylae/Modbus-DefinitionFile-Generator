import re
from dataclasses import dataclass
import pdfplumber

@dataclass
class ModbusRegister:
    """Holds structured data for a single Modbus register."""
    index: int = 0
    name: str = ""
    access: str = "RO"
    type: str = ""
    unit: str = ""
    gain: float = 1.0
    address: int = 0
    num_reg: int = 0
    scope: str = "" # Not used in final CSV but parsed for context

    def to_csv_row(self):
        """Converts the dataclass instance to a semicolon-separated CSV row."""
        info1 = 3  # Holding Register

        info2 = str(self.address)
        if self.type == 'STR':
            byte_size = self.num_reg * 2
            info2 = f"{self.address}_{byte_size}"

        info3 = self.type
        info4 = "" # Scale Factor not used

        tag_name = self.name.replace('[', '').replace(']', '').replace('.', '')
        tag = "".join(word.capitalize() for word in re.findall(r'\b\w+\b', tag_name.lower()))

        coef_a = self.gain
        coef_a_str = f"{coef_a:.10f}".rstrip('0').rstrip('.') if coef_a != 1.0 else "1"

        ordered_fields = [
            self.index, info1, info2, info3, info4,
            self.name, tag, coef_a_str, 0, self.unit, 4
        ]
        return ";".join(map(str, ordered_fields))

def _parse_table_row(row_cells):
    """
    Parses a list of cells from a table row into a ModbusRegister object.
    """
    # A valid row must start with a digit and have at least 9 columns, which is the structure of our target table.
    if not row_cells or not row_cells[0] or not row_cells[0].strip().isdigit() or len(row_cells) < 9:
        return None

    cells = [cell.replace('\n', ' ').strip() if cell else "" for cell in row_cells]

    try:
        reg = ModbusRegister(index=int(cells[0]))
        reg.name = cells[1]
        reg.access = cells[2]
        reg.type = cells[3]
        reg.unit = cells[4]

        gain_str = cells[5]
        if gain_str.isdigit():
            gain_val = int(gain_str)
            reg.gain = 1.0 / gain_val if gain_val != 0 else 1.0

        reg.address = int(cells[6])
        reg.num_reg = int(cells[7])
        reg.scope = cells[8]

        return reg
    except (ValueError, IndexError):
        return None

def parse_modbus_text(filepath):
    """
    Opens a PDF and parses it using pdfplumber's table extraction with
    a text-based strategy, which is more robust for tables without clear lines.
    """
    all_rows = []
    try:
        with pdfplumber.open(filepath) as pdf:
            start_page, end_page = -1, len(pdf.pages)
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if "3 Register Definitions" in page_text and start_page == -1:
                    if "4 Customized Interfaces" not in page_text:
                        start_page = i
                if "4 Customized Interfaces" in page_text and start_page != -1:
                    end_page = i
                    break

            if start_page == -1:
                print("Error: Could not find '3 Register Definitions' section.")
                return []

            table_settings = {
                "vertical_strategy": "text",
                "horizontal_strategy": "text",
            }

            for i in range(start_page, end_page):
                page = pdf.pages[i]
                tables = page.extract_tables(table_settings)
                for table in tables:
                    all_rows.extend(table)

    except Exception as e:
        print(f"An error occurred during PDF processing: {e}")
        return []

    registers = []
    last_reg = None
    for row in all_rows:
        # If a row doesn't start with a number, it's likely a continuation of the previous row's scope.
        if row and (row[0] is None or not row[0].strip().isdigit()) and last_reg:
            continuation_text = " ".join(filter(None, [cell.strip() if cell else None for cell in row]))
            if continuation_text:
                last_reg.scope += " " + continuation_text
        else:
            reg = _parse_table_row(row)
            if reg:
                registers.append(reg)
                last_reg = reg
            else:
                last_reg = None

    print(f"Parsing complete. Found {len(registers)} registers.")
    return registers

def generate_csv_data(registers, header_info):
    """
    Generates the content of the Webdyn CSV file from parsed registers.
    """
    header = ";".join(str(v) for v in header_info.values())
    lines = [header]
    for reg in registers:
        lines.append(reg.to_csv_row())
    return "\n".join(lines)
