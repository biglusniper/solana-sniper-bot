import os
import time
import requests

print("Starting bot...")

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
BIRDEYE_API_KEY = os.getenv("BIRDEYE_API_KEY")

print("DISCORD_WEBHOOK_URL:", "Loaded ✅" if DISCORD_WEBHOOK_URL else "❌ MISSING")
print("BIRDEYE_API_KEY:", "Loaded ✅" if BIRDEYE_API_KEY else "❌ MISSING")

if not DISCORD_WEBHOOK_URL or not BIRDEYE_API_KEY:
    print("❌ Missing required environment variables.")
    exit()

