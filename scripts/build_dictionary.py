"""Report the dictionary built from the database.

The dictionary is no longer a file: `core.attack` builds the candidate guesses
in memory from the base words in the database. This script just prints the
figures for the report (base words and |W|).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import dictionary
from core import attack


def report():
    bases = dictionary.base_words()
    candidates = attack.build_candidates()
    print("Base words (from the database usernames/emails):")
    print("  " + ", ".join(sorted(bases)))
    print(f"Total base words: {len(bases):,}")
    print(f"Expanded dictionary |W|: {len(candidates):,}")
    return len(candidates)


if __name__ == "__main__":
    report()
