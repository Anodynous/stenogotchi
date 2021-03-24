# Find HID keycode mapping here: https://www.usb.org/sites/default/files/documents/hut1_12v2.pdf
# Linux keycode : HID keycode

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
    # Keypad keys mapped by Plover
    94  : 197,  # "Keypad <"    # not working, shift(,) should work instead. Added as special case for send_string().
    126 : 215,  # "Keypad ±"    # tested ok
    187 : 182,  # "Keypad ("    # not working, shift(9) should work instead. Added as special case for send_string().
    188 : 183,  # "Keypad )"    # not working, shift(0) should work instead. Added as special case for send_string().
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

""" Plover keymap debug
TODO make modular instead of hardcoded translation to HID.

keymap:
linux keycode:shift modifier

9:0=ff1b[]          # Escape
10:0=31[1]
10:1=21[!]
11:0=32[2]
11:1=40[@]
12:0=33[3]
12:1=23[#]
13:0=34[4]
13:1=24[$]
14:0=35[5]
14:1=25[%]
15:0=36[6]
15:1=5e[^]
16:0=37[7]
16:1=26[&]
17:0=38[8]
17:1=2a[*]
18:0=39[9]
19:0=30[0]
20:0=2d[-]
20:1=5f[_]
21:0=3d[=]
21:1=2b[+]
22:0=ff08[]         # Backspace
23:0=ff09[     ]    # Tab
23:1=fe20[]         # Backtab
24:0=71[q]
24:1=51[Q]
25:0=77[w]
25:1=57[W]
26:0=65[e]
26:1=45[E]
27:0=72[r]
27:1=52[R]
28:0=74[t]
28:1=54[T]
29:0=79[y]
29:1=59[Y]
30:0=75[u]
30:1=55[U]
31:0=69[i]
31:1=49[I]
32:0=6f[o]
32:1=4f[O]
33:0=70[p]
33:1=50[P]
34:0=5b[[]
34:1=7b[{]
35:0=5d[]]
35:1=7d[}]
]36:0=ff0d[         # Return
37:0=ffe3[]         # Caps Lock ?
38:0=61[a]
38:1=41[A]
39:0=73[s]
39:1=53[S]
40:0=64[d]
40:1=44[D]
41:0=66[f]
41:1=46[F]
42:0=67[g]
42:1=47[G]
43:0=68[h]
43:1=48[H]
44:0=6a[j]
44:1=4a[J]
45:0=6b[k]
45:1=4b[K]
46:0=6c[l]
46:1=4c[L]
47:0=3b[;]
47:1=3a[:]
48:0=27[']
48:1=22["]
49:0=60[`]
49:1=7e[~]
50:0=ffe1[]         # Shift ?
51:0=5c[\]
51:1=7c[|]
52:0=7a[z]
52:1=5a[Z]
53:0=78[x]
53:1=58[X]
54:0=63[c]
54:1=43[C]
55:0=76[v]
55:1=56[V]
56:0=62[b]
56:1=42[B]
57:0=6e[n]
57:1=4e[N]
58:0=6d[m]
58:1=4d[M]
59:0=2c[,]
60:0=2e[.]
60:1=3e[>]
61:0=2f[/]
61:1=3f[?]
94:0=3c[<]
126:0=b1[±]
187:0=28[(]
188:0=29[)]
"""