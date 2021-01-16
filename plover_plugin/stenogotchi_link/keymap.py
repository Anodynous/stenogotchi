plover_keytable = {
    # Function row.
    67: 58,    #"F1",
    68: 59,    #"F2",
    69: 60,    #"F3",
    70: 61,    #"F4",
    71: 62,    #"F5",
    72: 63,    #"F6",
    73: 64,    #"F7",
    74: 65,    #"F8",
    75: 66,    #"F9",
    76: 67,    #"F10",
    95: 68,    #"F11",
    96: 69,    #"F12",
    # Number row.
    49: 53,    #"`",
    10: 30,    #"1",
    11: 31,    #"2",
    12: 32,    #"3",
    13: 33,    #"4",
    14: 34,    #"5",
    15: 35,    #"6",
    16: 36,    #"7",
    17: 37,    #"8",
    18: 38,    #"9",
    19: 39,    #"0",
    20: 45,    #"-",
    21: 46,    #"=",
    51: 50,    #"\\",
    # Upper row.
    24: 20,    #"q",
    25: 26,    #"w",
    26: 8,     #"e",
    27: 21,    #"r",
    28: 23,    #"t",
    29: 28,    #"y",
    30: 24,    #"u",
    31: 12,    #"i",
    32: 18,    #"o",
    33: 19,    #"p",
    34: 47,    #"[",
    35: 48,    #"]",
    # Home row.
    38: 4,     #"a",
    39: 22,    #"s",
    40: 7,     #"d",
    41: 9,     #"f",
    42: 10,    #"g",
    43: 11,    #"h",
    44: 13,    #"j",
    45: 14,    #"k",
    46: 15,    #"l",
    47: 51,    #";",
    48: 52,    #"'",
    # Bottom row.
    52: 29,    #"z",
    53: 27,    #"x",
    54: 6,     #"c",
    55: 25,    #"v",
    56: 5,     #"b",
    57: 17,    #"n",
    58: 16,    #"m",
    59: 54,    #",",
    60: 55,    #".",
    61: 56,    #"/",
    # Other keys.
    22 : 42,    #"BackSpace",
    119: 76,    #"Delete",
    116: 81,    #"Down",
    115: 77,    #"End",
    9  : 41,    #"Escape",
    110: 74,    #"Home",
    118: 73,    #"Insert",
    113: 80,    #"Left",
    117: 78,    #"Page_Down",
    112: 75,    #"Page_Up",
    36 : 40,    #"Return",
    114: 79,    #"Right",
    23 : 43,    #"Tab",
    111: 82,    #"Up",
    65 : 44,    #"space",
}

# Map modifier keys to array element in the bit array
plover_modkeys = {
    "KEY_RIGHTMETA": 0,
    "KEY_RIGHTALT": 1,
    "KEY_RIGHTSHIFT": 2,
    "KEY_RIGHTCTRL": 3,
    "KEY_LEFTMETA": 4,
    "KEY_LEFTALT": 5,
    1 : 6,               #"KEY_LEFTSHIFT"
    "KEY_LEFTCTRL": 7
}

def plover_convert(plover_keycode):
    return plover_keytable[plover_keycode]

def plover_modkey(plover_keycode):
    if plover_keycode in plover_modkeys:
        return plover_modkeys[plover_keycode]
    else:
        return -1  # Return an invalid array element