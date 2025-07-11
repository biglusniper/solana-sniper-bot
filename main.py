import os
import time

print("Step 1: Bot starting...")

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
BIRDEYE_API_KEY = os.getenv("BIRDEYE_API_KEY")

print("Step 2: Environment variables loaded")
print("DISCORD_WEBHOOK_URL:", DISCORD_WEBHOOK_URL)
print("BIRDEYE_API_KEY:", BIRDEYE_API_KEY)

print("Step 3: Sleeping 10 seconds...")
time.sleep(10)

print("Step 4: Finished test run.")
