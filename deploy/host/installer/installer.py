"""Compatibility launcher for the canonical NoeRelay provision command."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'src'))
from noerelay.cli import main
if __name__ == '__main__':
    sys.argv.insert(1, 'provision')
    main()
