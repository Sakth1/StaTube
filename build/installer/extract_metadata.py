#!/usr/bin/env python3
"""
Extract APP_* metadata from main.py
Outputs KEY=VALUE lines for GitHub Actions step outputs.
"""
import re
import sys
from pathlib import Path

if len(sys.argv) < 2:
    print("Usage: extract_metadata.py <main.py>")
    sys.exit(2)

path = Path(sys.argv[1])
if not path.exists():
    print(f"Error: File not found: {path}")
    sys.exit(2)

text = path.read_text(encoding="utf-8")

patterns = {
    "APP_NAME": r'APP_NAME\s*=\s*[\'"]([^\'"]+)[\'"]',
    "APP_VERSION": r'APP_VERSION\s*=\s*[\'"]([^\'"]+)[\'"]',
    "APP_PUBLISHER": r'APP_PUBLISHER\s*=\s*[\'"]([^\'"]+)[\'"]',
    "APP_DESCRIPTION": r'APP_DESCRIPTION\s*=\s*[\'"]([^\'"]+)[\'"]',
}

values = {}

for key, pattern in patterns.items():
    match = re.search(pattern, text)
    if not match:
        print(f"Error: {key} not found in {path}")
        sys.exit(3)
    values[key] = match.group(1)

for key, value in values.items():
    print(f"{key}={value}")
