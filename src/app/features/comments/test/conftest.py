import sys
from pathlib import Path


# Ensure the project "src" directory is on sys.path so imports like "app.*" resolve
PROJECT_SRC = Path(__file__).resolve().parents[4]
if str(PROJECT_SRC) not in sys.path:
    sys.path.append(str(PROJECT_SRC))
