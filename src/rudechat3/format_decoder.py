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
            case '\x16':
                existing_colours = [attr for attr in current_attributes if attr.colour or attr.background]
                if existing_colours:
                    # Assuming there is at most one colour and background attribute at any time
                    current_colour = existing_colours[0].colour
                    current_background = existing_colours[0].background
                    # Clear existing color and background
                    current_attributes = [attr for attr in current_attributes if not (attr.colour or attr.background)]
                    # Swap the colors
                    current_attributes.append(Attribute(colour=current_background, background=current_colour))
                else:
                    # If no colors were set, default to swapping black (01) and white (00)
                    current_attributes.append(Attribute(colour=1, background=0))
            case '\x03':
                current_attributes = []
                
                # Extracting color and background codes using regex
                match = re.match(r'(\d{1,2})(?:,(\d{1,2}))?', input_text[c_index + 1:])
                
                if match:
                    colour_code = match.group(1)
                    background_code = match.group(2) if match.group(2) else ''
                    c_index += len(match.group(0))
                    
                    # Converting codes to integers
                    try:
                        colour = int(colour_code)
                        background = int(background_code) if background_code else 1
                    except ValueError:
                        pass
                    else:
                        new_attribute = Attribute(colour=colour, background=background)
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
