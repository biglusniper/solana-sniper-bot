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

SLEEP_TIME = 60
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
        response = requests.post(DISCORD_WEBHOOK_URL, json=message)
        if response.status_code != 204:
            print("Discord webhook error:", response.status_code, response.text)
        else:
            print(f"Sent alert for {token.get('symbol')}")
    except Exception as e:
        print("Discord send error:", e)

# 🔁 Replace your old check_birdeye() with this new one:
def check_birdeye():
    print("Checking Birdeye...")

    try:
        url = "https://public-api.birdeye.so/public/token/solana/trending"
        headers = {"X-API-KEY": BIRDEYE_API_KEY}
        res = requests.get(url, headers=headers)

        print("Response status:", res.status_code)
        print("Raw response text:", res.text[:300])

        if res.status_code != 200:
            print("Birdeye API error:", res.status_code)
            return

        data = res.json()
        trending = data.get("data", [])

        print(f"Found {len(trending)} tokens")

        for token in trending:
            try:
                liq = token.get("liquidity", 0)
                vol = token.get("volume", 0)
                holders = token.get("holders", 0)

                if liq > MIN_VOLUME and vol > MIN_VOLUME and holders >= MIN_HOLDERS:
                    print(f"Passing: {token.get('symbol')} - ${liq:,} LP, {holders} holders")
                    send_alert(token)
                else:
                    print(f"Skipped: {token.get('symbol')} - LP ${liq:,}, Holders {holders}")
            except Exception as token_err:
                print("Token loop error:", token_err)

    except Exception as e:
        print("Main API error:", e)

# 🔁 Main loop
while True:
    check_birdeye()
    time.sleep(SLEEP_TIME)
