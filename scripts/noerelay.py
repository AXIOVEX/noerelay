"""Repository entry point; implementation lives in src/noerelay (no stale CLI copy)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from noerelay.cli import main
if __name__ == "__main__":
    main()
