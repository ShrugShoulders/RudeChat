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
        ICON_FILE = os.path.join(G_CONFIG_DIR, 'Resources/Icons/rude_icon_roundedge.png')
    case "Windows":
        ICON_FILE = os.path.join(G_SOURCE_DIR, 'Resources/Icons/rude.ico')
    case _:
        ICON_FILE = os.path.join(G_CONFIG_DIR, 'Resources/Icons/rude_icon_roundedge.png')
