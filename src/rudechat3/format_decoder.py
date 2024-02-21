import dataclasses
from typing import List, Tuple

@dataclasses.dataclass(frozen=True)
class Attribute:
    bold: bool = False
    italic: bool = False
    underline: bool = False
    strikethrough: bool = False
    colour: int = 0
    background: int = 0

def decoder(input_text: str) -> List[Tuple[str, List[Attribute]]]:
    output = []
    current_text = ""
    current_attributes = []
    c_index = 0

    while c_index < len(input_text):
        c = input_text[c_index]
        match c:
            case '\x02':
                if not any(attr.bold for attr in current_attributes):
                    current_attributes.append(Attribute(bold=True))
            case '\x1D':
                if not any(attr.italic for attr in current_attributes):
                    current_attributes.append(Attribute(italic=True))
            case '\x1F':
                if not any(attr.underline for attr in current_attributes):
                    current_attributes.append(Attribute(underline=True))
            case '\x1E':
                if not any(attr.strikethrough for attr in current_attributes):
                    current_attributes.append(Attribute(strikethrough=True))
            case '\x03':
                current_attributes = []
                colour_code = ''
                while c_index + 1 < len(input_text) and input_text[c_index + 1].isdigit():
                    c_index += 1
                    colour_code += input_text[c_index]
                if colour_code:
                    background_num = 0
                    if c_index + 1 < len(input_text) and input_text[c_index + 1] == ',':
                        c_index += 1
                        background_code = ''
                        while c_index + 1 < len(input_text) and input_text[c_index + 1].isdigit():
                            c_index += 1
                            background_code += input_text[c_index]
                        try:
                            background_num = int(background_code)
                        except ValueError:
                            background_num = 0
                    new_attribute = Attribute(colour=int(colour_code), background=background_num)
                    if new_attribute not in current_attributes:
                        current_attributes.append(new_attribute)
            case '\x0F':
                current_attributes = []
            case _:
                current_text += c

        # Check for the end of the string
        if c_index == len(input_text) - 1:
            current_attributes = []

        if current_text:
            output.append((current_text, list(current_attributes)))
            current_text = ''

        c_index += 1

    return output
