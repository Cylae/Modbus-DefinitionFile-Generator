import re
from dataclasses import dataclass

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

def parse_modbus_text(text_content):
    """
    Parses the raw text of a Modbus documentation to extract register information.
    """
    print("Starting parse_modbus_text...")
    registers = []
    lines = text_content.splitlines()

    start_index = -1
    for i, line in enumerate(lines):
        if "3 Register Definitions" in line:
            start_index = i + 2
            print(f"Found table start at line {start_index}")
            break

    if start_index == -1:
        print("Error: Could not find '3 Register Definitions' section.")
        return []

    current_line_data = ""
    for line in lines[start_index:]:
        if "4 Customized Interfaces" in line:
            print("Found end of table.")
            break

        line = line.strip()
        if not line:
            continue

        if re.match(r"^\d+", line):
            if current_line_data:
                reg = _parse_register_line(current_line_data)
                if reg:
                    registers.append(reg)
            current_line_data = line
        else:
            current_line_data += " " + line

    if current_line_data:
        reg = _parse_register_line(current_line_data)
        if reg:
            registers.append(reg)

    print(f"Parsing complete. Found {len(registers)} registers.")
    return registers

def _parse_register_line(line):
    """Helper function to parse a single, consolidated line of register data."""
    print(f"Attempting to parse line: '{line}'")
    try:
        pattern = re.compile(
            r"^(?P<index>\d+)\s+"
            r"(?P<name_and_rest>.+)"
        )
        match = pattern.match(line)
        if not match:
            print("  [FAIL] Initial pattern did not match.")
            return None

        index = int(match.group('index'))
        name_and_rest = match.group('name_and_rest')

        # Find address and num_reg from the right
        addr_match = re.search(r'(?P<address>\d{5,})\s+(?P<num_reg>\d+)\s*(?P<scope>.*)$', name_and_rest)
        if not addr_match:
            print("  [FAIL] Could not find address and num_reg at the end of the line.")
            return None

        address = int(addr_match.group('address'))
        num_reg = int(addr_match.group('num_reg'))
        scope = addr_match.group('scope').strip()

        # The part between the start and the address info
        middle_part = name_and_rest[:addr_match.start()].strip()

        # Split the middle part to find access, type, unit, gain
        parts = re.split(r'\s+', middle_part)

        access = parts[-2]
        type = parts[-1].replace("Sec ond", "Second")

        name_parts = parts[:-2]

        reg = ModbusRegister(index=index, address=address, num_reg=num_reg, scope=scope, access=access, type=type)

        # Heuristics for Unit and Gain from the name parts
        if len(name_parts) > 1:
            # Check if last part of name is a gain
            try:
                gain_divisor = float(name_parts[-1])
                reg.gain = 1.0 / gain_divisor
                name_parts.pop()
            except ValueError:
                pass # Not a number

        if len(name_parts) > 1:
            # Check if new last part is a unit
            if re.fullmatch(r'[a-zA-Z°%/]+', name_parts[-1]):
                reg.unit = name_parts.pop()

        reg.name = " ".join(name_parts)

        print(f"  [SUCCESS] Parsed: {reg.name}")
        return reg

    except Exception as e:
        print(f"  [CRITICAL] Unhandled exception in _parse_register_line for line '{line}': {e}")
        return None

def generate_csv_data(registers, header_info):
    """
    Generates the content of the Webdyn CSV file from parsed registers.
    """
    header = ";".join(str(v) for v in header_info.values())

    lines = [header]
    for reg in registers:
        lines.append(reg.to_csv_row())

    return "\n".join(lines)
