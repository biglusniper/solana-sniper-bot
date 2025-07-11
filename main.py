import requests
import time

DISCORD_WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK"
BIRDEYE_API_KEY = "YOUR_BIRDEYE_API_KEY"
MIN_VOLUME = 100
MIN_HOLDERS = 2
SLEEP_TIME = 60

def send_alert(token):
    message = {
        "content": (
            "New Token Detected\n"
            f"Name: {token.get('name', 'N/A')}\n"
            f"Symbol: {token.get('symbol', 'N/A')}\n"
            f"Liquidity: ${int(float(token.get('liquidity', 0))):,}\n"
            f"Holders: {int(float(token.get('holders', 0)))}\n"
            f"Volume (24h): ${int(float(token.get('volume_24h', 0))):,}\n"
            f"Link: https://birdeye.so/token/{token.get('address', '')}"
        )
    }
    requests.post(DISCORD_WEBHOOK_URL, json=message)

def check_birdeye():
    try:
        res = requests.get(
            "https://public-api.birdeye.so/v1/token/solana/top-volume",
            headers={"x-chain": "solana", "X-API-KEY": BIRDEYE_API_KEY}
        )
        if res.status_code != 200:
            print("Birdeye API error:", res.status_code, res.text)
            return
        data = res.json()
        tokens = data.get("data", [])
        print("Found", len(tokens), "tokens")
        for token in tokens:
            liq = float(token.get("liquidity", 0))
            vol = float(token.get("volume_24h", 0))
            holders = float(token.get("holders", 0))
            status = token.get('symbol', 'N/A')
            if liq > MIN_VOLUME and vol > MIN_VOLUME and holders >= MIN_HOLDERS:
                print("Passing:", status)
                send_alert(token)
            else:
                print("Skipped:", status)
    except Exception as err:
        print("Error:", err)

while True:
    check_birdeye()
    time.sleep(SLEEP_TIME)
