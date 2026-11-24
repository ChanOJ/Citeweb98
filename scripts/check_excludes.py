#!/usr/bin/env python3
"""Fail if site/ holds engine code, backups or server markers that must never be published."""
import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "site"
BAD_EXT = {".asp", ".inc", ".dll", ".exe", ".bat", ".ctw", ".bak", ".lck", ".psd", ".tga", ".txt~"}
BAD_TEXT = re.compile(rb"<%|<!--\s*#include|<form\b|<input\b", re.I)
errors = []
for p in sorted(SITE.rglob("*")):
    if not p.is_file():
        continue
    if p.suffix.lower() in BAD_EXT:
        errors.append("forbidden file: %s" % p.relative_to(SITE))
    elif p.suffix.lower() in {".htm", ".html"} and BAD_TEXT.search(p.read_bytes()):
        errors.append("server markup or form in %s" % p.relative_to(SITE))
if errors:
    sys.exit("\n".join(errors))
print("check_excludes: ok")
