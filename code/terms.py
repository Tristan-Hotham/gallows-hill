"""The name classes. Each class is a case-insensitive regular expression tested on OS Open Names
name1 and name2 (the Welsh or Gaelic alternative name, where there is one).

A match means only "the name contains these letters". No claim is made here about what any single
name means. Gallows and Gibbet are the main, strong classes. Hangman is a weaker class. Hanging is a
contrast class: in English place names "hanging" very often describes a steep slope (a hanging wood),
so it is analysed separately and never pooled with the others.

Run `python3 code/terms.py` to see the tests pass.
"""
import re

# key: (label, strength, regex, exclude regex or None)
CLASSES = {
    "gallows": ("Gallows / Gallow", "strong", r"gallow", r"galloway"),
    "gibbet":  ("Gibbet",           "strong", r"gibbet", None),
    "hangman": ("Hangman",          "weak",   r"hangman", None),
    "hanging": ("Hanging",          "contrast", r"\bhanging", None),
}
ORDER = list(CLASSES)
STRONG = ["gallows", "gibbet"]
_C = {k: (re.compile(v[2], re.I), re.compile(v[3], re.I) if v[3] else None) for k, v in CLASSES.items()}
# any name containing these is kept out of the matched "ordinary name" pool
ANY_GRIM = re.compile(r"gallow|gibbet|hang|tyburn|stocks|pillory|murder|dead ?m[ae]n", re.I)


def classify(name):
    """Return the first class key found in one name, or None."""
    for k, (rx, ex) in _C.items():
        if rx.search(name) and not (ex and ex.search(name)):
            return k
    return None


if __name__ == "__main__":
    tests = {
        "Gallows Hill": "gallows", "Gallow Hill": "gallows", "Gallowhill Wood": "gallows",
        "Gallowstree Common": "gallows", "Mull of Galloway": None, "Gibbet Hill": "gibbet",
        "Near Gibbet Dale": "gibbet", "Hangman's Wood": "hangman", "Great Hangman": "hangman",
        "Hanging Wood": "hanging", "Hangingshaw Hill": "hanging", "The Hanger": None, "Clayhanger": None,
        "White Hill": None,
    }
    for n, want in tests.items():
        got = classify(n)
        assert got == want, (n, got, want)
    print(f"{len(tests)} tests passed")
