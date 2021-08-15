# Find HID keycode mapping here: https://www.usb.org/sites/default/files/documents/hut1_12v2.pdf
# Linux keycodes can be found in /usr/share/X11/xkb/keycodes/evdev

# Linux keycode used by Plover : HID keycode used for BT
plover_keytable = {
    # Function row.
    67: 58,     #"F1",
    68: 59,     #"F2",
    69: 60,     #"F3",
    70: 61,     #"F4",
    71: 62,     #"F5",
    72: 63,     #"F6",
    73: 64,     #"F7",
    74: 65,     #"F8",
    75: 66,     #"F9",
    76: 67,     #"F10",
    95: 68,     #"F11",
    96: 69,     #"F12",
    # Number row.
    49: 53,     #"`",
    10: 30,     #"1",
    11: 31,     #"2",
    12: 32,     #"3",
    13: 33,     #"4",
    14: 34,     #"5",
    15: 35,     #"6",
    16: 36,     #"7",
    17: 37,     #"8",
    18: 38,     #"9",
    19: 39,     #"0",
    20: 45,     #"-",
    21: 46,     #"=",
    51: 50,     #"\\",
    # Upper row.
    24: 20,     #"q",
    25: 26,     #"w",
    26: 8,      #"e",
    27: 21,     #"r",
    28: 23,     #"t",
    29: 28,     #"y",
    30: 24,     #"u",
    31: 12,     #"i",
    32: 18,     #"o",
    33: 19,     #"p",
    34: 47,     #"[",
    35: 48,     #"]",
    # Home row.
    38: 4,      #"a",
    39: 22,     #"s",
    40: 7,      #"d",
    41: 9,      #"f",
    42: 10,     #"g",
    43: 11,     #"h",
    44: 13,     #"j",
    45: 14,     #"k",
    46: 15,     #"l",
    47: 51,     #";",
    48: 52,     #"'",
    # Bottom row.
    52: 29,     #"z",
    53: 27,     #"x",
    54: 6,      #"c",
    55: 25,     #"v",
    56: 5,      #"b",
    57: 17,     #"n",
    58: 16,     #"m",
    59: 54,     #",",
    60: 55,     #".",
    61: 56,     #"/",
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
    65 : 44,    #"Space",
    66 : 57,     #Caps_Lock,
    #"KEY_BACK": 241,
    #"KEY_FORWARD": 242,
    #"KEY_REFRESH": 250,
    #"KEY_SYSRQ": 70,
    # Keypad keys
    #"KEY_NUMLOCK": 83,
    #"KEY_SCROLLLOCK": 71,
    79: 95,     #kp_7 - "KEY_KP7"
    80: 96,     #kp_8 - "KEY_KP8"
    81: 97,     #kp_9 - "KEY_KP9"
    #"KEY_KPMINUS": 86,
    83: 92,     #kp_4 - "KEY_KP4"
    84: 93,     #kp_5 - "KEY_KP5"
    85: 94,     #kp_6 - "KEY_KP6"
    #"KEY_KPPLUS": 87,
    87: 89,     #kp_1 - "KEY_KP1"
    88: 90,     #kp_2 - "KEY_KP2"
    89: 91,     #kp_3 - "KEY_KP3"
    90: 98,     #kp_0 - "KEY_KP0"
    126: 215,   # "Keypad ±"
    #"KEY_KPDOT": 99,
    #94 : 197,   # "Keypad <"    # not working, shift(,) added as special case for send_string() instead.
    #187: 182,   # "Keypad ("    # not working, shift(9) added as special case for send_string() instead.
    #188: 183,   # "Keypad )"    # not working, shift(0) added as special case for send_string() instead.

    
    # TODO: Media keys not working correctly
    # Media keys
    172: 232,   # AudioPlay - "KEY_PLAYPAUSE"
    209: 232,   # AudioPause - "KEY_PLAYPAUSE"
    121: 239,   # AudioMute - "KEY_MUTE"
    122: 238,   #AudioLowerVolume - "KEY_VOLUMEDOWN"
    123: 237,   #AudioRaiseVolume - "KEY_VOLUMEUP"
    173: 234,   #AudioPrev - "KEY_PREVIOUSSONG"
    171: 235,   #AudioNext - "KEY_NEXTSONG"
    174: 233,   #AudioStop - "KEY_STOPCD"
    169: 236,   #Eject - "KEY_EJECTCD"
}

# Map modifier keys to array element in the bit array
plover_modkeys = {
    134: 0,     #Super_R - "KEY_RIGHTMETA", WIN-key
    108: 1,     #"KEY_RIGHTALT"
    62: 2,      #"KEY_RIGHTSHIFT"
    105: 3,     #"KEY_RIGHTCTRL"
    133: 4,     #Super_L - "KEY_LEFTMETA", WIN-key
    64: 5,      #"KEY_LEFTALT"
    50 : 6,     #"KEY_LEFTSHIFT"
    1 : 6,      #"KEY_LEFTSHIFT", mapped to both 50 and 1 as '1' is used by Plover as shift modifier to capitalize letters and '50' when sent in key-combo
    37: 7       #"KEY_LEFTCTRL"
}

def plover_convert(plover_keycode):
    if plover_keycode in plover_keytable:
        return plover_keytable[plover_keycode]
    else:
        return -1  # Return an invalid keycode

def plover_modkey(plover_keycode):
    if plover_keycode in plover_modkeys:
        return plover_modkeys[plover_keycode]
    else:
        return -1  # Return an invalid array element  