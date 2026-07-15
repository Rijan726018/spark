import sys
from pathlib import Path

# Add project root to path so imports resolve without install
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
