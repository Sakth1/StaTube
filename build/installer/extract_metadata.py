#!/usr/bin/env python3
"""Extract APP_NAME, APP_VERSION, APP_PUBLISHER, APP_DESCRIPTION from main.py
Outputs to stdout and writes build/installer/metadata.out
"""
import re
import sys
from pathlib import Path


if len(sys.argv) < 2:
print("Usage: extract_metadata.py <path-to-main.py>")
sys.exit(2)


p = Path(sys.argv[1])
if not p.exists():
print(f"File not found: {p}")
sys.exit(2)


text = p.read_text(encoding='utf-8')


patterns = {
'APP_NAME': r"APP_NAME\s*=\s*['\"]([^'\"]+)['\"]",
'APP_VERSION': r"APP_VERSION\s*=\s*['\"]([^'\"]+)['\"]",
'APP_PUBLISHER': r"APP_PUBLISHER\s*=\s*['\"]([^'\"]+)['\"]",
'APP_DESCRIPTION': r"APP_DESCRIPTION\s*=\s*['\"]([^'\"]+)['\"]",
}


outputs = {}
for key, pat in patterns.items():
m = re.search(pat, text)
if not m:
print(f"ERROR: {key} not found in {p}. Please add {key} constant to main.py")
sys.exit(3)
outputs[key] = m.group(1)


out = Path('build/installer/metadata.out')
out.parent.mkdir(parents=True, exist_ok=True)
with out.open('w', encoding='utf-8') as f:
for k, v in outputs.items():
f.write(f"{k}={v}\n")


for k, v in outputs.items():
print(f"{k}={v}")


print('Metadata extracted and saved to build/installer/metadata.out')
