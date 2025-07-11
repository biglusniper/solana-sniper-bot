import requests
import time
import os

print("Starting bot...")  # Add this line at the top

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
BIRDEYE_API_KEY = os.getenv("BIRDEYE_API_KEY")

MIN_VOLUME = 100
MIN_HOLDERS = 2
SLEEP_TIME = 60  # seconds

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
            print(f"Alert sent for {token.get('symbol')}")
    except Exception as err:
        print("Error sending to Discord:", err)

def check_birdeye():
    print("Running Birdeye check...")
    try:
        url = "https://public-api.birdeye.so/public/token/solana/trending"
        headers = {"X-API-KEY": BIRDEYE_API_KEY}
        res = requests.get(url, headers=headers)

        if res.status_code != 200:
            print("Birdeye API error:", res.status_code, res.text)
            return

        trending = res.json().get("data", [])
        print(f"Found {len(trending)} tokens")

        for token in trending:
            try:
                liq = token.get("liquidity", 0)
                vol = token.get("volume", 0)
                holders = token.get("holders", 0)

                if liq > MIN_VOLUME and vol > MIN_VOLUME and holders >= MIN_HOLDERS:
                    print(f"Passing: {token['symbol']} - ${liq:,} LP, {holders} holders")
                    send_alert(token)
                else:
                    print(f"Skipped: {token.get('symbol', 'N/A')} - LP ${liq:,}, Holders {holders}")
            except Exception as token_err:
                print("Token loop error:", token_err)

    except Exception as outer_err:
        print("Main API error:", outer_err)

# Run in loop
while True:
    check_birdeye()
    time.sleep(SLEEP_TIME)
