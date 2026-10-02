"""Arabic letters as rasm + decoration.

Decoration tokens (see core.apply_decor):
    a1 a2 a3 a3r a4 a2v a3h     dots above (3 = pointing up, 3r = pointing down)
    b1 b2 b3 b3r b4 b2v b3h     dots below (3 = pointing down, 3r = pointing up)
    tah v iv hamza madda wasla dalef damma whamza   small marks above
    tahb vb ivb hamzab whamzab                      small marks below
    ring hh bar                                     placed at rasm points
A decoration may differ for initial/medial forms: use a dict
{'isol': [...], 'init': [...], ...} or the shorthand ('isolfina', 'initmedi').
"""
from __future__ import annotations

import re
import unicodedata


def F(isolfina, initmedi=None):
    initmedi = isolfina if initmedi is None else initmedi
    return {"isol": isolfina, "fina": isolfina, "init": initmedi, "medi": initmedi}


# codepoint -> (rasm, decoration)
LETTERS = {
    0x0620: ("yeh", F(["ring"], ["b2"])),
    0x0621: ("hamza", []),
    0x0622: ("alef", ["madda"]),
    0x0623: ("alef", ["hamza"]),
    0x0624: ("waw", ["hamza"]),
    0x0625: ("alef", ["hamzab"]),
    0x0626: ("yeh", ["hamza"]),
    0x0627: ("alef", []),
    0x0628: ("beh", ["b1"]),
    0x0629: ("hehR", ["a2"]),
    0x062A: ("beh", ["a2"]),
    0x062B: ("beh", ["a3"]),
    0x062C: ("hah", ["b1"]),
    0x062D: ("hah", []),
    0x062E: ("hah", ["a1"]),
    0x062F: ("dal", []),
    0x0630: ("dal", ["a1"]),
    0x0631: ("reh", []),
    0x0632: ("reh", ["a1"]),
    0x0633: ("seen", []),
    0x0634: ("seen", ["a3"]),
    0x0635: ("sad", []),
    0x0636: ("sad", ["a1"]),
    0x0637: ("tah", []),
    0x0638: ("tah", ["a1"]),
    0x0639: ("ain", []),
    0x063A: ("ain", ["a1"]),
    0x063B: ("keheh", ["a2"]),
    0x063C: ("keheh", ["b3"]),
    0x063D: ("yeh", F(["iv"], ["b2", "iv"])),
    0x063E: ("yeh", ["a2"]),
    0x063F: ("yeh", ["a3"]),
    0x0641: ("feh", ["a1"]),
    0x0642: ("qaf", ["a2"]),
    0x0643: ("kaf", []),
    0x0644: ("lam", []),
    0x0645: ("meem", []),
    0x0646: ("noon", ["a1"]),
    0x0647: ("heh", []),
    0x0648: ("waw", []),
    0x0649: ("yeh", []),
    0x064A: ("yeh", ["b2"]),
    0x066E: ("beh", []),
    0x066F: ("qaf", []),
    0x0671: ("alef", ["wasla"]),
    0x0672: ("alef", ["whamza"]),
    0x0673: ("alef", ["whamzab"]),
    0x0674: ("highhamza", []),
    0x0675: ("alef", ["hh"]),
    0x0676: ("waw", ["hh"]),
    0x0677: ("waw", ["damma", "hh"]),
    0x0678: ("yeh", ["hh"]),
    0x0679: ("beh", ["tah"]),
    0x067A: ("beh", ["a2v"]),
    0x067B: ("beh", ["b2v"]),
    0x067C: ("beh", ["a2", "ring"]),
    0x067D: ("beh", ["a3r"]),
    0x067E: ("beh", ["b3"]),
    0x067F: ("beh", ["a4"]),
    0x0680: ("beh", ["b4"]),
    0x0681: ("hah", ["hamza"]),
    0x0682: ("hah", ["a2v"]),
    0x0683: ("hah", ["b2"]),
    0x0684: ("hah", ["b2v"]),
    0x0685: ("hah", ["a3"]),
    0x0686: ("hah", ["b3"]),
    0x0687: ("hah", ["b4"]),
    0x0688: ("dal", ["tah"]),
    0x0689: ("dal", ["ring"]),
    0x068A: ("dal", ["b1"]),
    0x068B: ("dal", ["tah", "b1"]),
    0x068C: ("dal", ["a2"]),
    0x068D: ("dal", ["b2"]),
    0x068E: ("dal", ["a3"]),
    0x068F: ("dal", ["a3r"]),
    0x0690: ("dal", ["a4"]),
    0x0691: ("reh", ["tah"]),
    0x0692: ("reh", ["v"]),
    0x0693: ("reh", ["ring"]),
    0x0694: ("reh", ["b1"]),
    0x0695: ("reh", ["vb"]),
    0x0696: ("reh", ["b1", "a1"]),
    0x0697: ("reh", ["a2"]),
    0x0698: ("reh", ["a3"]),
    0x0699: ("reh", ["a4"]),
    0x069A: ("seen", ["b1", "a1"]),
    0x069B: ("seen", ["b3"]),
    0x069C: ("seen", ["b3", "a3"]),
    0x069D: ("sad", ["b2"]),
    0x069E: ("sad", ["a3"]),
    0x069F: ("tah", ["a3"]),
    0x06A0: ("ain", ["a3"]),
    0x06A1: ("feh", []),
    0x06A2: ("feh", ["b1"]),
    0x06A3: ("feh", ["a1", "b1"]),
    0x06A4: ("feh", ["a3"]),
    0x06A5: ("feh", ["b3"]),
    0x06A6: ("feh", ["a4"]),
    0x06A7: ("qaf", ["a1"]),
    0x06A8: ("qaf", ["a3"]),
    0x06A9: ("keheh", []),
    0x06AA: ("kafswash", []),
    0x06AB: ("keheh", ["ring"]),
    0x06AC: ("kaf", ["a1"]),
    0x06AD: ("kaf", ["a3"]),
    0x06AE: ("kaf", ["b3"]),
    0x06AF: ("gaf", []),
    0x06B0: ("gaf", ["ring"]),
    0x06B1: ("gaf", ["a2"]),
    0x06B2: ("gaf", ["b2"]),
    0x06B3: ("gaf", ["b2v"]),
    0x06B4: ("gaf", ["a3"]),
    0x06B5: ("lam", ["v"]),
    0x06B6: ("lam", ["a1"]),
    0x06B7: ("lam", ["a3"]),
    0x06B8: ("lam", ["b3"]),
    0x06B9: ("noon", ["a1", "b1"]),
    0x06BA: ("noon", F([], ["a1"])),
    0x06BB: ("noon", ["tah"]),
    0x06BC: ("noon", ["a1", "ring"]),
    0x06BD: ("noon", ["a3"]),
    0x06BE: ("hehdo", []),
    0x06BF: ("hah", ["b3", "a1"]),
    0x06C0: ("hehR", ["hamza"]),
    0x06C1: ("hehgoal", []),
    0x06C2: ("hehgoal", ["hamza"]),
    0x06C3: ("hehgoalR", ["a2"]),
    0x06C4: ("waw", ["ring"]),
    0x06C5: ("waw", ["bar"]),
    0x06C6: ("waw", ["v"]),
    0x06C7: ("waw", ["damma"]),
    0x06C8: ("waw", ["dalef"]),
    0x06C9: ("waw", ["iv"]),
    0x06CA: ("waw", ["a2"]),
    0x06CB: ("waw", ["a3"]),
    0x06CC: ("yeh", F([], ["b2"])),
    0x06CD: ("yehR", ["bar"]),
    0x06CE: ("yeh", F(["v"], ["b2", "v"])),
    0x06CF: ("waw", ["a1"]),
    0x06D0: ("yeh", ["b2v"]),
    0x06D1: ("yeh", ["b3"]),
    0x06D2: ("yehbarree", []),
    0x06D3: ("yehbarree", ["hamza"]),
    0x06D5: ("hehR", []),
    0x06EE: ("dal", ["iv"]),
    0x06EF: ("reh", ["iv"]),
    0x06FA: ("seen", ["b1", "a3"]),
    0x06FB: ("sad", ["b1", "a1"]),
    0x06FC: ("ain", ["b1", "a1"]),
    0x06FF: ("heh", ["iv"]),
}

# --- supplement blocks from character names --------------------------------

_BASES = [
    ("FARSI YEH", "yeh", []), ("YEH BARREE", "yehbarree", []), ("YEH", "yeh", []),
    ("BEH", "beh", []), ("TEH", "beh", ["a2"]), ("PEH", "beh", ["b3"]), ("TTEH", "beh", ["tah"]),
    ("JEEM", "hah", ["b1"]), ("HAH", "hah", []), ("TCHEH", "hah", ["b3"]),
    ("DAL", "dal", []), ("REH", "reh", []), ("ZAIN", "reh", ["a1"]),
    ("SEEN", "seen", []), ("SAD", "sad", []), ("TAH", "tah", []),
    ("AIN", "ain", []), ("GHAIN", "ain", ["a1"]), ("FEH", "feh", []), ("QAF", "qaf", []),
    ("KEHEH", "keheh", []), ("KAF", "kaf", []), ("GAF", "gaf", []), ("LAM", "lam", []),
    ("MEEM", "meem", []), ("NOON", "noon", []), ("WAW", "waw", []), ("ALEF", "alef", []),
]

_PHRASES = [
    ("THREE DOTS POINTING UPWARDS BELOW", "b3r"), ("THREE DOTS POINTING DOWNWARDS ABOVE", "a3r"),
    ("THREE DOTS HORIZONTALLY BELOW", "b3h"), ("TWO DOTS VERTICALLY ABOVE", "a2v"),
    ("TWO DOTS VERTICALLY BELOW", "b2v"), ("THREE DOTS ABOVE", "a3"), ("THREE DOTS BELOW", "b3"),
    ("FOUR DOTS ABOVE", "a4"), ("FOUR DOTS BELOW", "b4"), ("TWO DOTS ABOVE", "a2"),
    ("TWO DOTS BELOW", "b2"), ("DOT ABOVE", "a1"), ("DOT BELOW", "b1"),
    ("INVERTED SMALL V BELOW", "ivb"), ("SMALL V BELOW", "vb"), ("INVERTED V ABOVE", "iv"),
    ("INVERTED V", "iv"), ("SMALL V", "v"), ("HAMZA ABOVE", "hamza"),
    ("SMALL ARABIC LETTER TAH BELOW", "tahb"), ("SMALL ARABIC LETTER TAH ABOVE", "tah"),
    ("SMALL ARABIC LETTER TAH AND TWO DOTS", "tah+a2"), ("SMALL ARABIC LETTER TAH", "tah"),
    ("SMALL TAH", "tah"), ("TWO DOTS", "a2"),
]

_SKIP_WORDS = ("DIGIT", "STROKE", "BAR", "LOOP", "WITHIN", "SMALL MEEM", "SMALL NOON", "SMALL TEH",
               "AFRICAN", "ROHINGYA", "LOW ALEF", "STRAIGHT", "GRAF", "NO DOTS")


def _parse(cp):
    try:
        nm = unicodedata.name(chr(cp))
    except ValueError:
        return None
    if not nm.startswith("ARABIC LETTER "):
        return None
    nm = nm[len("ARABIC LETTER "):]
    if any(w in nm for w in _SKIP_WORDS):
        return None
    base, _, rest = nm.partition(" WITH ")
    for bname, rasm, dec in _BASES:
        if base == bname:
            break
    else:
        return None
    toks = list(dec)
    rest = rest.replace(" AND ", "|")
    for part in [p for p in rest.split("|") if p]:
        for ph, tk in _PHRASES:
            if part == ph:
                toks += tk.split("+")
                break
        else:
            return None
    return rasm, toks


for _cp in list(range(0x0750, 0x0780)) + list(range(0x08A0, 0x08C8)):
    _r = _parse(_cp)
    if _r is not None and _cp not in LETTERS:
        LETTERS[_cp] = _r
# qaf "with dot below" keeps its own dots in Unicode's naming
if 0x08A5 in LETTERS:
    LETTERS[0x08A5] = ("qaf", ["a2", "b1"])
