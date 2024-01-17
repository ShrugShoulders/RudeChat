import dataclasses
from typing import List, Tuple

@dataclasses.dataclass(frozen=True)
class Attribute:
    bold: bool = False
    italic: bool = False
    underline: bool = False
    colour: int = 0
    background: int = 0

def decoder(input_text: str) -> List[Tuple[str, List[Attribute]]]:
    output = []
    current_text = ""
    current_attributes = []
    attribute_stack = []
    c_index = 0
    color_start_index = None
    color_end_index = None
    color_tag = None

    while c_index < len(input_text):
        c = input_text[c_index]
        match c:
            case '\x02':
                if not any(attr.bold for attr in current_attributes):
                    current_attributes.append(Attribute(bold=True))
                    attribute_stack.append(Attribute(bold=True))
                else:
                    current_attributes = [a for a in current_attributes if not a.bold]
                    attribute_stack.pop()
            case '\x1D':
                if not any(attr.italic for attr in current_attributes):
                    current_attributes.append(Attribute(italic=True))
                    attribute_stack.append(Attribute(italic=True))
                else:
                    current_attributes = [a for a in current_attributes if not a.italic]
                    attribute_stack.pop()
            case '\x1F':
                if not any(attr.underline for attr in current_attributes):
                    current_attributes.append(Attribute(underline=True))
                    attribute_stack.append(Attribute(underline=True))
                else:
                    current_attributes = [a for a in current_attributes if not a.underline]
                    attribute_stack.pop()
            case '\x03':
                colour_code = ''
                for _ in range(2):
                    if c_index + 1 < len(input_text) and input_text[c_index + 1].isdigit():
                        c_index += 1
                        colour_code += input_text[c_index]
                    else:
                        break
                if colour_code:
                    # Check if a comma follows the color code for background color
                    if c_index + 1 < len(input_text) and input_text[c_index + 1] == ',':
                        c_index += 1
                        background_code = ''
                        for _ in range(2):
                            if c_index + 1 < len(input_text) and input_text[c_index + 1].isdigit():
                                c_index += 1
                                background_code += input_text[c_index]
                            else:
                                break
                        background_num = int(background_code)
                        current_attributes.append(Attribute(colour=int(colour_code), background=background_num))
                        attribute_stack.append(Attribute(colour=int(colour_code), background=background_num))
                    else:
                        colour_num = int(colour_code)
                        current_attributes.append(Attribute(colour=colour_num))
                        attribute_stack.append(Attribute(colour=colour_num))
                    # Track the start index of color
                    color_start_index = c_index
                else:
                    # If no digit follows '\x03', treat it as the end of color
                    color_end_index = c_index
                    current_attributes.clear()
                    attribute_stack.clear()

                    # Check if the color control is open and close it
                    if color_start_index is not None and color_end_index is None:
                        output.append(("", current_attributes))
            case '\x0F':
                current_attributes.clear()
                attribute_stack.clear()
            case _:
                current_text += c

        if attribute_stack:
            current_attributes = attribute_stack[:]

        if current_text:
            output.append((current_text, current_attributes[:]))
            current_text = ''

        c_index += 1

    # Check if the color control is open and close it
    if color_start_index is not None and color_end_index is None:
        current_attributes.clear()
        attribute_stack.clear()
        output.append(("", current_attributes))

    return output