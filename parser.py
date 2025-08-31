import re
from dataclasses import dataclass, fields
import pdfplumber
from pdfminer.pdfparser import PDFSyntaxError

# --- Keyword & Dataclass Definitions ---

# Defines the canonical names for columns and the keywords to find them in a PDF.
# This allows for flexible matching across different languages and document formats.
HEADER_KEYWORDS = {
    "index": ["no", "index", "#"],
    "name": ["name", "signal", "description", "parameter", "libellé"],
    "access": ["access", "r/w", "read/write", "accès"],
    "type": ["type", "typ", "data type", "format"],
    "unit": ["unit", "un.", "units", "unité"],
    "gain": ["gain", "scale", "factor", "scaling", "multiplier"],
    "address": ["address", "addre", "register", "reg."],
    "num_reg": ["num", "number"],
    "scope": ["scope", "comments", "remarques"],
}

# Defines keywords that indicate the end of the Modbus registers section.
STOP_KEYWORDS = ["alarm", "event", "customized interface", "error code"]


class ParserError(Exception):
    """Custom exception for parsing errors."""
    pass


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
    scope: str = ""

    def to_csv_row(self):
        """Converts the dataclass instance to a semicolon-separated CSV row."""
        info1 = 3  # Holding Register
        info2 = str(self.address)
        if self.type == 'STR':
            byte_size = self.num_reg * 2
            info2 = f"{self.address}_{byte_size}"
        info3 = self.type
        info4 = ""  # Scale Factor not used
        tag_name = self.name.replace('[', '').replace(']', '').replace('.', '')
        tag = "".join(word.capitalize() for word in re.findall(r'\b\w+\b', tag_name.lower()))
        coef_a = self.gain
        coef_a_str = f"{coef_a:.10f}".rstrip('0').rstrip('.') if coef_a != 1.0 else "1"
        ordered_fields = [
            self.index, info1, info2, info3, info4,
            self.name, tag, coef_a_str, 0, self.unit, 4
        ]
        return ";".join(map(str, ordered_fields))

# --- Parsing Logic ---

def _is_header_row(row, combined_header):
    """
    Checks if a given row is a plausible header row by matching keywords.
    Returns a column map if it's a header, otherwise None.
    """
    if not row:
        return None
    column_map = {}
    for canonical_name, keywords in HEADER_KEYWORDS.items():
        for col_idx, cell_text in enumerate([str(c).lower() for c in row]):
            if any(keyword in cell_text for keyword in keywords):
                if canonical_name not in column_map:
                    column_map[canonical_name] = col_idx

    # A header is considered plausible if it contains at least 4 of the defined columns.
    if len(column_map) >= 4:
        # Heuristic: If 'gain' is missing but 'type' is present, they might be in a merged cell.
        if 'gain' not in column_map and 'type' in column_map and 'gain' in combined_header:
            column_map['gain'] = column_map['type']
        return column_map
    return None

def _is_stop_header(row):
    """
    Checks if a row is a header for a new section (e.g., "4.1 Alarms"),
    which indicates that we should stop parsing.
    """
    # A section title typically has very few columns. Data rows have more.
    if not row or len(row) >= 5:
        return False

    cleaned_row_text = " ".join([str(cell).lower().replace('\n', ' ') for cell in row if cell]).strip()
    # Check if the row starts with a number (like "4.1" or "5.") and contains a stop keyword.
    if re.match(r'^\d+(\.\d*)*\s*', cleaned_row_text):
        if any(stop_word in cleaned_row_text for stop_word in STOP_KEYWORDS):
            return True
    return False

def _parse_row_with_map(row_cells, column_map):
    """
    Parses a single row of a table into a ModbusRegister object using the provided column map.
    Returns the object or None if it's not a valid data row.
    """
    index_col = column_map.get("index")
    # A valid data row must have an integer in the 'index' column.
    if index_col is None or index_col >= len(row_cells) or not str(row_cells[index_col]).strip().isdigit():
        return None

    reg_data = {}
    for canonical_name, col_idx in column_map.items():
        if col_idx < len(row_cells):
            cell_value = row_cells[col_idx]
            reg_data[canonical_name] = cell_value.replace('\n', ' ').strip() if cell_value else ""

    valid_fields = {f.name for f in fields(ModbusRegister)}
    filtered_reg_data = {k: v for k, v in reg_data.items() if k in valid_fields}

    try:
        reg = ModbusRegister(**filtered_reg_data)
        # Robustly handle type conversions for numeric fields.
        try:
            gain_str = reg_data.get('gain', '1.0')
            gain_val = float(gain_str)
            reg.gain = 1.0 / gain_val if gain_val != 0 else 1.0
        except (ValueError, TypeError):
            reg.gain = 1.0  # Default to 1.0 if gain is not a valid number (e.g., text).

        reg.index = int(float(reg_data.get('index', 0)))
        reg.address = int(float(reg_data.get('address', 0)))
        reg.num_reg = int(float(reg_data.get('num_reg', 0)))

        # Automatically set num_reg to 2 for 32-bit data types if not specified
        # This makes the parser more robust against incomplete documentation.
        thirty_two_bit_types = {'int32', 'uint32', 'float32'}
        if reg.type.lower().strip() in thirty_two_bit_types and reg.num_reg < 2:
            reg.num_reg = 2

        return reg
    except (ValueError, TypeError):
        return None # Return None if essential numeric conversions fail.

def parse_modbus_text(filepath):
    """
    Main parsing function. Opens a PDF and extracts Modbus registers.
    It works by iterating through all tables and maintaining a state.
    """
    registers = []
    last_reg = None
    column_map = None
    parsing_started = False

    try:
        with pdfplumber.open(filepath) as pdf:
            table_settings = {"vertical_strategy": "text", "horizontal_strategy": "text"}
            for page in pdf.pages:
                tables = page.extract_tables(table_settings)
                for table in tables:
                    if not table: continue

                    if parsing_started and _is_stop_header(table[0]):
                        # Stop parsing if a stop header is found in a new table
                        if not registers: continue # Avoid stopping if we haven't found anything yet
                        return registers

                    for i, row in enumerate(table):
                        if not parsing_started:
                            combined_header = " ".join([str(c).lower().replace('\n', ' ') for c in row])
                            header_map = _is_header_row(row, combined_header)
                            if header_map:
                                if "address" not in header_map or "name" not in header_map:
                                    continue # Not a valid Modbus table header
                                column_map = header_map
                                parsing_started = True
                                for data_row in table[i+1:]:
                                    reg = _parse_row_with_map(data_row, column_map)
                                    if reg:
                                        registers.append(reg)
                                        last_reg = reg
                                    elif last_reg:
                                        continuation_text = " ".join(str(c).strip() for c in data_row if c is not None)
                                        if continuation_text:
                                            last_reg.scope = (last_reg.scope + " " + continuation_text).strip()
                                break
                        elif parsing_started:
                            reg = _parse_row_with_map(row, column_map)
                            if reg:
                                registers.append(reg)
                                last_reg = reg
                            elif last_reg:
                                continuation_text = " ".join(str(c).strip() for c in row if c is not None)
                                if continuation_text:
                                    last_reg.scope = (last_reg.scope + " " + continuation_text).strip()
    except PDFSyntaxError as e:
        raise ParserError(f"Erreur de syntaxe PDF: Le fichier est peut-être corrompu.\n({e})")
    except Exception as e:
        # Catch other potential errors during processing
        raise ParserError(f"Une erreur inattendue est survenue lors du traitement du PDF.\n({e})")

    if not parsing_started:
        raise ParserError("Aucun en-tête de tableau Modbus valide n'a été trouvé dans le document.")

    return registers

def generate_csv_data(registers, header_info):
    """Generates the final CSV content from a list of registers."""
    header = ";".join(str(v) for v in header_info.values())
    lines = [header]
    for reg in registers:
        lines.append(reg.to_csv_row())
    return "\n".join(lines)
