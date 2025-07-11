import os
import time
import requests

print("Step 1: Bot starting...")

# Load environment variables
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
BIRDEYE_API_KEY = os.getenv("BIRDEYE_API_KEY")

if not DISCORD_WEBHOOK_URL or not BIRDEYE_API_KEY:
    print("❌ Missing environment variables")
    exit()
else:
    print("Step 2: Environment variables loaded")
    print("DISCORD_WEBHOOK_URL:", DISCORD_WEBHOOK_URL)
    print("BIRDEYE_API_KEY:", BIRDEYE_API_KEY)

SLEEP_TIME = 60  # seconds
MIN_VOLUME = 100
MIN_HOLDERS = 2

def send_alert(token):
    message = {
        "content": f"New Token Detected\n"
                   f"Name: {token.get('name', 'N/A')}\n"
                   f"Symbol: {token.get('symbol', 'N/A')}\n"
                   f"LP: ${token.get('liquidity', 0):,}\n"
                   f"Holders: {token.get('holders', 0)}\n"
                   f"Volume (5m): ${token.get('volume', 0):,}\n"
                   f"Link: https://birdeye.so/token/{token.get('address', '')}"
    }
    try:
        res = requests.post(DISCORD_WEBHOOK_URL, json=message)
        print("✅ Alert sent:", token.get('symbol'), "Status:", res.status_code)
    except Exception as e:
        print("❌ Webhook error:", e)

def check_birdeye():
    print("Step 3: Checking Birdeye trending tokens...")

    url = "https://public-api.birdeye.so/defi/trending"
    headers = {
        "X-API-KEY": BIRDEYE_API_KEY,
        "x-chain": "solana"
    }

    try:
        res = requests.get(url, headers=headers)
        print("Status Code:", res.status_code)

        if res.status_code != 200:
            print("❌ Birdeye API error:", res.text)
            return

        data = res.json()
        tokens = data.get("data", [])

        print(f"Found {len(tokens)} tokens")

        for token in tokens:
            liq = token.get("liquidity", 0)
            vol = token.get("volume", 0)
            holders = token.get("holders", 0)

            if liq > MIN_VOLUME and vol > MIN_VOLUME and holders >= MIN_HOLDERS:
                print(f"✅ PASS: {token['symbol']} | LP: ${liq:,} | Holders: {holders}")
                send_alert(token)
            else:
                print(f"⏩ SKIP: {token.get('symbol')} | LP: ${liq:,} | Holders: {holders}")

    except Exception as e:
        print("❌ Birdeye fetch error:", e)

print("Sleeping 5 seconds before test run...")
time.sleep(5)
print("Starting test run...\n")

check_birdeye()

print("✅ Test run finished.")
