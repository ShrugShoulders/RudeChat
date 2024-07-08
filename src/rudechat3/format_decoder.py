import dataclasses
import re
from typing import List, Tuple

@dataclasses.dataclass(frozen=True)
class Attribute:
    bold: bool = False
    italic: bool = False
    underline: bool = False
    strikethrough: bool = False
    inverse: bool = False 
    colour: int = 0
    background: int = 1

def decoder(pattern, input_text: str) -> List[Tuple[str, List[Attribute]]]:
    output = []
    current_attributes = []

    for match in pattern.finditer(input_text):
        token = match.group(0)

        if token == '\x02':
            if not any(attr.bold for attr in current_attributes):
                current_attributes.append(Attribute(bold=True))
        elif token == '\x1D':
            if not any(attr.italic for attr in current_attributes):
                current_attributes.append(Attribute(italic=True))
        elif token == '\x1F':
            if not any(attr.underline for attr in current_attributes):
                current_attributes.append(Attribute(underline=True))
        elif token == '\x1E':
            if not any(attr.strikethrough for attr in current_attributes):
                current_attributes.append(Attribute(strikethrough=True))
        elif token == '\x16':
            existing_colours = [attr for attr in current_attributes if attr.colour or attr.background]
            if existing_colours:
                current_colour = existing_colours[0].colour
                current_background = existing_colours[0].background
                current_attributes = [attr for attr in current_attributes if not (attr.colour or attr.background)]
                current_attributes.append(Attribute(colour=current_background, background=current_colour))
            else:
                current_attributes.append(Attribute(colour=1, background=0))
        elif token.startswith('\x03'):
            current_attributes = []
            colour_code, background_code = '', ''
            codes = token[1:].split(',')
            if len(codes) > 0 and codes[0].isdigit():
                colour_code = codes[0]
            if len(codes) > 1 and codes[1].isdigit():
                background_code = codes[1]
            try:
                colour = int(colour_code)
                background = int(background_code) if background_code else 1
            except ValueError:
                pass
            else:
                current_attributes.append(Attribute(colour=colour, background=background))
        elif token == '\x0F':
            current_attributes = []
        else:
            output.append((token, list(current_attributes)))

    return output