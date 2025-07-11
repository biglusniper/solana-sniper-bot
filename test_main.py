# test_main.py
import sys
import os

# Force immediate flush for all print statements
# This might not be necessary given the latest Python 3.13.4,
# but it's good for ensuring prints aren't buffered.
sys.stdout.reconfigure(line_buffering=True) if sys.version_info >= (3, 7) else None

print("TEST_DEBUG: Script started! (from test_main.py)", flush=True)
print(f"TEST_DEBUG: Current working directory: {os.getcwd()}", flush=True)

try:
    import requests
    print("TEST_DEBUG: requests imported successfully.", flush=True)
except ImportError as e:
    print(f"TEST_DEBUG: ERROR: Failed to import requests: {e}", flush=True)
    sys.exit(1) # Exit with an error code to make it clear it failed
except Exception as e:
    print(f"TEST_DEBUG: An unexpected error during import: {e}", flush=True)
    sys.exit(1) # Exit with an error code

print("TEST_DEBUG: Script finishing test.", flush=True)
# The script will now just exit, we don't need a loop for this test.
