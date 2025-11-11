#!/usr/bin/env python3

from rudechat4.shared_imports import *

G_SOURCE_DIR = os.path.dirname(os.path.abspath(__file__))
G_CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "rudechat")

#IRC Formats
IRC_FORMAT = [
    ("Bold", "\x02"),
    ("Italic", "\x1D"),
    ("Underline", "\x1F"),
    ("Strike Through", "\x1E"),
    ("Inverse", "\x16")
]

ANSI_TO_IRC_MAP = {
    # Foreground Colors (30-37, ANSI Dark)
    # ANSI Color:     Black, Red, Green, Yellow, Blue, Magenta, Cyan, White/Gray
    # IRC Index:      01,    04,  03,    08,     02,   06,      10,   14 
    30: 1, 31: 4, 32: 3, 33: 7, 34: 2, 35: 6, 36: 10, 37: 14,
    
    # Background Colors (40-47, ANSI Dark)
    # IRC Index:      01,    04,  03,    08,     02,   06,      10,   14 
    40: 1, 41: 4, 42: 3, 43: 7, 44: 2, 45: 6, 46: 10, 47: 14,
    
    # Bright Foreground Colors (90-97, ANSI Bright)
    # IRC Index:      08,    05,  09,    11,     12,   13,      11,   00 (or 15)
    90: 8, 91: 5, 92: 9, 93: 11, 94: 12, 95: 13, 96: 11, 97: 0, # Use 0 (White) for Bright White
    
    # Bright Background Colors (100-107, ANSI Bright)
    # IRC Index:      08,    05,  09,    11,     12,   13,      11,   00 (or 15)
    100: 8, 101: 5, 102: 9, 103: 11, 104: 12, 105: 13, 106: 11, 107: 0,
}

ANSI_256_COLOR_MAP = {
    # 0-15: Standard 16 ANSI Colors (Terminal Dependent, but these are typical defaults)
    # The first 8 are standard, the next 8 (8-15) are the bright/high-intensity versions.
    0:  '#000000', # Black
    1:  '#800000', # Red
    2:  '#008000', # Green
    3:  '#808000', # Yellow
    4:  '#000080', # Blue
    5:  '#800080', # Magenta
    6:  '#008080', # Cyan
    7:  '#c0c0c0', # White / Light Gray
    8:  '#808080', # Bright Black / Dark Gray
    9:  '#ff0000', # Bright Red
    10: '#00ff00', # Bright Green
    11: '#ffff00', # Bright Yellow
    12: '#0000ff', # Bright Blue
    13: '#ff00ff', # Bright Magenta
    14: '#00ffff', # Bright Cyan
    15: '#ffffff', # Bright White

    # 16-231: 6x6x6 RGB Color Cube (216 colors)
    # The value is calculated as 16 + 36*r + 6*g + b, where r, g, b are in [0, 1, 2, 3, 4, 5]
    16:  '#000000', 17:  '#00005f', 18:  '#000087', 19:  '#0000af', 20:  '#0000d7', 21:  '#0000ff',
    22:  '#005f00', 23:  '#005f5f', 24:  '#005f87', 25:  '#005faf', 26:  '#005fd7', 27:  '#005fff',
    28:  '#008700', 29:  '#00875f', 30:  '#008787', 31:  '#0087af', 32:  '#0087d7', 33:  '#0087ff',
    34:  '#00af00', 35:  '#00af5f', 36:  '#00af87', 37:  '#00afaf', 38:  '#00afd7', 39:  '#00afff',
    40:  '#00d700', 41:  '#00d75f', 42:  '#00d787', 43:  '#00d7af', 44:  '#00d7d7', 45:  '#00d7ff',
    46:  '#00ff00', 47:  '#00ff5f', 48:  '#00ff87', 49:  '#00ffaf', 50:  '#00ffd7', 51:  '#00ffff',
    
    52:  '#5f0000', 53:  '#5f005f', 54:  '#5f0087', 55:  '#5f00af', 56:  '#5f00d7', 57:  '#5f00ff',
    58:  '#5f5f00', 59:  '#5f5f5f', 60:  '#5f5f87', 61:  '#5f5faf', 62:  '#5f5fd7', 63:  '#5f5fff',
    64:  '#5f8700', 65:  '#5f875f', 66:  '#5f8787', 67:  '#5f87af', 68:  '#5f87d7', 69:  '#5f87ff',
    70:  '#5faf00', 71:  '#5faf5f', 72:  '#5faf87', 73:  '#5fafaf', 74:  '#5fafd7', 75:  '#5fafff',
    76:  '#5fd700', 77:  '#5fd75f', 78:  '#5fd787', 79:  '#5fd7af', 80:  '#5fd7d7', 81:  '#5fd7ff',
    82:  '#5fff00', 83:  '#5fff5f', 84:  '#5fff87', 85:  '#5fffaf', 86:  '#5fffd7', 87:  '#5fffff',
    
    88:  '#870000', 89:  '#87005f', 90:  '#870087', 91:  '#8700af', 92:  '#8700d7', 93:  '#8700ff',
    94:  '#875f00', 95:  '#875f5f', 96:  '#875f87', 97:  '#875faf', 98:  '#875fd7', 99:  '#875fff',
    100: '#878700', 101: '#87875f', 102: '#878787', 103: '#8787af', 104: '#8787d7', 105: '#8787ff',
    106: '#87af00', 107: '#87af5f', 108: '#87af87', 109: '#87afaf', 110: '#87afd7', 111: '#87afff',
    112: '#87d700', 113: '#87d75f', 114: '#87d787', 115: '#87d7af', 116: '#87d7d7', 117: '#87d7ff',
    118: '#87ff00', 119: '#87ff5f', 120: '#87ff87', 121: '#87ffaf', 122: '#87ffd7', 123: '#87ffff',
    
    124: '#af0000', 125: '#af005f', 126: '#af0087', 127: '#af00af', 128: '#af00d7', 129: '#af00ff',
    130: '#af5f00', 131: '#af5f5f', 132: '#af5f87', 133: '#af5faf', 134: '#af5fd7', 135: '#af5fff',
    136: '#af8700', 137: '#af875f', 138: '#af8787', 139: '#af87af', 140: '#af87d7', 141: '#af87ff',
    142: '#afaf00', 143: '#afaf5f', 144: '#afaf87', 145: '#afafaf', 146: '#afafd7', 147: '#afafff',
    148: '#afd700', 149: '#afd75f', 150: '#afd787', 151: '#afd7af', 152: '#afd7d7', 153: '#afd7ff',
    154: '#afff00', 155: '#afff5f', 156: '#afff87', 157: '#afffaf', 158: '#afffd7', 159: '#afffff',
    
    160: '#d70000', 161: '#d7005f', 162: '#d70087', 163: '#d700af', 164: '#d700d7', 165: '#d700ff',
    166: '#d75f00', 167: '#d75f5f', 168: '#d75f87', 169: '#d75faf', 170: '#d75fd7', 171: '#d75fff',
    172: '#d78700', 173: '#d7875f', 174: '#d78787', 175: '#d787af', 176: '#d787d7', 177: '#d787ff',
    178: '#d7af00', 179: '#d7af5f', 180: '#d7af87', 181: '#d7afaf', 182: '#d7afd7', 183: '#d7afff',
    184: '#d7d700', 185: '#d7d75f', 186: '#d7d787', 187: '#d7d7af', 188: '#d7d7d7', 189: '#d7d7ff',
    190: '#d7ff00', 191: '#d7ff5f', 192: '#d7ff87', 193: '#d7ffaf', 194: '#d7ffd7', 195: '#d7ffff',
    
    196: '#ff0000', 197: '#ff005f', 198: '#ff0087', 199: '#ff00af', 200: '#ff00d7', 201: '#ff00ff',
    202: '#ff5f00', 203: '#ff5f5f', 204: '#ff5f87', 205: '#ff5faf', 206: '#ff5fd7', 207: '#ff5fff',
    208: '#ff8700', 209: '#ff875f', 210: '#ff8787', 211: '#ff87af', 212: '#ff87d7', 213: '#ff87ff',
    214: '#ffaf00', 215: '#ffaf5f', 216: '#ffaf87', 217: '#ffafaf', 218: '#ffafd7', 219: '#ffafff',
    220: '#ffd700', 221: '#ffd75f', 222: '#ffd787', 223: '#ffd7af', 224: '#ffd7d7', 225: '#ffd7ff',
    226: '#ffff00', 227: '#ffff5f', 228: '#ffff87', 229: '#ffffaf', 230: '#ffffd7', 231: '#ffffff',
    
    # 232-255: Grayscale Ramp (24 colors)
    232: '#080808', 233: '#121212', 234: '#1c1c1c', 235: '#262626', 236: '#303030', 237: '#3a3a3a',
    238: '#444444', 239: '#4e4e4e', 240: '#585858', 241: '#626262', 242: '#6c6c6c', 243: '#767676',
    244: '#808080', 245: '#8a8a8a', 246: '#949494', 247: '#9e9e9e', 248: '#a8a8a8', 249: '#b2b2b2',
    250: '#bcbcbc', 251: '#c6c6c6', 252: '#d0d0d0', 253: '#dadaDA', 254: '#e4e4e4', 255: '#eeeeee',
}

#IRC Colors
IRC_COLORS = {
    "White": "00",
    "Black": "01",
    "Blue": "02",
    "Green": "03",
    "Red": "04",
    "Brown": "05",
    "Purple": "06",
    "Orange": "07",
    "Yellow": "08",
    "Light Green": "09",
    "Cyan": "10",
    "Light Cyan": "11",
    "Light Blue": "12",
    "Pink": "13",
    "Grey": "14",
    "Light Grey": "15",
    "Navy Blue": "16",
    "Dark Blue": "17",
    "Medium Blue": "18",
    "Deep Blue": "19",
    "Dark Green": "20",
    "Sea Green": "21",
    "Forest Green": "22",
    "Olive": "23",
    "Maroon": "24",
    "Dark Red": "25",
    "Fire Red": "26",
    "Rust": "27",
    "Dark Orange": "28",
    "Burnt Orange": "29",
    "Dark Brown": "30",
    "Chocolate": "31",
    "Dark Purple": "32",
    "Indigo": "33",
    "Violet": "34",
    "Magenta": "35",
    "Rose": "36",
    "Hot Pink": "37",
    "Salmon": "38",
    "Peach": "39",
    "Gold": "40",
    "Khaki": "41",
    "Tan": "42",
    "Beige": "43",
    "Cream": "44",
    "Light Yellow": "45",
    "Pale Yellow": "46",
    "Lime": "47",
    "Mint": "48",
    "Teal": "49",
    "Sky Blue": "50",
    "Baby Blue": "51",
    "Azure": "52",
    "Ice Blue": "53",
    "Powder Blue": "54",
    "Periwinkle": "55",
    "Lilac": "56",
    "Lavender": "57",
    "Blush": "58",
    "Coral": "59",
    "Tomato": "60",
    "Crimson": "61",
    "Brick Red": "62",
    "Wine": "63",
    "Rust Brown": "64",
    "Copper": "65",
    "Amber": "66",
    "Mustard": "67",
    "Honey": "68",
    "Sand": "69",
    "Moss": "70",
    "Avocado": "71",
    "Jade": "72",
    "Turquoise": "73",
    "Ocean Blue": "74",
    "Denim": "75",
    "Slate Blue": "76",
    "Steel Blue": "77",
    "Orchid": "78",
    "Fuchsia": "79",
    "Plum": "80",
    "Mulberry": "81",
    "Berry": "82",
    "Rosewood": "83",
    "Mahogany": "84",
    "Brick": "85",
    "Clay": "86",
    "Taupe": "87",
    "Dove Grey": "88",
    "Ash": "89",
    "Charcoal": "90",
    "Coal": "91",
    "Gunmetal": "92",
    "Smoke": "93",
    "Silver": "94",
    "Frost": "95",
    "Cloud": "96",
    "Snow": "97",
    "Ivory": "98"
}

# Create the folder if it doesn't exist
if not os.path.exists(G_CONFIG_DIR):
    os.makedirs(G_CONFIG_DIR)

match platform.system():
    case "Darwin" | "Linux":
        ICON_FILE = os.path.join(G_SOURCE_DIR, 'Resources/Icons/rude_icon_roundedge.png')
    case "Windows":
        ICON_FILE = os.path.join(G_SOURCE_DIR, 'Resources/Icons/rude.ico')
    case _:
        ICON_FILE = os.path.join(G_SOURCE_DIR, 'Resources/Icons/rude_icon_roundedge.png')
