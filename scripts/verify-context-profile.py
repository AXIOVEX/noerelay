"""Verify allocated context on every route and exercise a longer coding prompt."""
from pathlib import Path
import runpy
ROOT = Path(__file__).resolve().parent
runpy.run_path(str(ROOT / 'verify-local-stack.py'), run_name='__main__')
runpy.run_path(str(ROOT / 'verify-long-context.py'), run_name='__main__')
