import requests
import time
import os

# Step 1: Load environment variables
print("Step 1: Bot starting...")

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
if not DISCORD_WEBHOOK_URL:
    print("❌ DISCORD_WEBHOOK_URL is missing")
    exit()

print("DISCORD_WEBHOOK_URL loaded ✅")

# Step 2: Config
MIN_LIQUIDITY = 1000
SLEEP_TIME = 60  # seconds

def send_alert(token):
    message = {
        "content": f"New Token Detected\n"
                   f"Name: {token.get('name', 'N/A')}\n"
                   f"Symbol: {token.get('symbol', 'N/A')}\n"
                   f"Liquidity: ${token.get('liquidity', 0):,.0f}\n"
                   f"🔗 https://birdeye.so/token/{token.get('address', '')}"
    }

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=message)
        if response.status_code != 204:
            print("❌ Discord webhook error:", response.status_code, response.text)
        else:
            print(f"✅ Sent alert for {token.get('symbol', 'N/A')}")
    except Exception as e:
        print("❌ Failed to send Discord alert:", e)

def check_birdeye():
    print("Step 3: Fetching Birdeye token list...")

    url = "https://public-api.birdeye.so/public/tokenlist?chain=solana"

    try:
        res = requests.get(url)
        print("Status Code:", res.status_code)

        if res.status_code != 200:
            print("❌ Birdeye API error:", res.text)
            return

        tokens = res.json().get("data", [])
        print(f"🔍 Found {len(tokens)} tokens...")

        for token in tokens[:20]:  # Check top 20 for speed
            liquidity = token.get("liquidity", 0)
            if liquidity > MIN_LIQUIDITY:
                send_alert(token)
            else:
                print(f"⏩ Skipping {token.get('symbol')} - liquidity ${liquidity:,.0f}")

    except Exception as e:
        print("❌ Error in Birdeye fetch:", e)

# Main loop
while True:
    check_birdeye()
    time.sleep(SLEEP_TIME)
