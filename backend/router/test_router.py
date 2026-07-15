import sys
import os

# Ensure the root directory is on the path so we can import 'backend.router'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.router.allocator import process_master_signal

if __name__ == "__main__":
    signal = "BUY 2 ES Contract at Market"
    print("Initiating PAMM distribution...")
    process_master_signal(signal)
    print("All tasks dispatched to the message broker.")
