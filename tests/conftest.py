import sys
from pathlib import Path

SRC = str(Path(__file__).resolve().parent.parent)
MOCKS = str(Path(__file__).resolve().parent / "_mocks")

for p in [SRC, MOCKS]:
    if p not in sys.path:
        sys.path.insert(0, p)