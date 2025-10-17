# backend/tests/conftest.py
import sys
from pathlib import Path

# Ensure the 'backend' directory is on sys.path so "import app" works
ROOT = Path(__file__).resolve().parents[1]  # backend/
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
