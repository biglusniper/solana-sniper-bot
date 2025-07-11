import requests
import time
import os
import sys
import traceback

if sys.version_info >= (3, 7):
    sys.stdout.reconfigure(line_buffering=True)

print("Bot starting...", flush=True)

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
if not DISCORD_WEBHOOK_URL:
    print("❌ DISCORD_WEBHOOK_URL is missing! Exiting.", flush=True)
    sys.exit(1)
print("Webhook loaded ✅", flush=True)

SLEEP_TIME = 60  # check every minute
PERCENT_GAIN_THRESHOLD = 30  # 1hr percent gain to be considered a "snipe"
MARKET_CAP_MAX = 20_000_000  # only smaller cap plays
VOLUME_MIN = 50000  # minimum 24h volume

def send_alert(token):
    message = {
        "content": f"🚀 Possible Snipe Alert!\n"
                   f"Name: {token['name']} ({token['symbol'].upper()})\n"
                   f"Price: ${token['current_price']:,}\n"
                   f"1H Change: {token['price_change_percentage_1h_in_currency']:.2f}%\n"
                   f"Market Cap: ${token['market_cap']:,}\n"
                   f"24h Volume: ${token['total_volume']:,}\n"
                   f"🔗 https://www.coingecko.com/en/coins/{token['id']}"
    }
    try:
        r = requests.post(DISCORD_WEBHOOK_URL, json=message)
        if r.status_code != 204:
            print(f"Webhook error {r.status_code}: {r.text}", flush=True)
        else:
            print(f"✅ Alert sent for {token['name']}", flush=True)
    except Exception as e:
        print("❌ Failed to send alert:", e, flush=True)

def fetch_snipes():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        'vs_currency': 'usd',
        'order': 'volume_desc',
        'per_page': 100,
        'page': 1,
        'price_change_percentage': '1h'
    }

    try:
        res = requests.get(url, params=params, timeout=15)
        if res.status_code != 200:
            print(f"API error: {res.status_code} - {res.text}", flush=True)
            return

        coins = res.json()
        print(f"Fetched {len(coins)} tokens", flush=True)

        for coin in coins:
            try:
                if (
                    coin.get('price_change_percentage_1h_in_currency') and
                    coin['price_change_percentage_1h_in_currency'] >= PERCENT_GAIN_THRESHOLD and
                    coin['market_cap'] and coin['market_cap'] < MARKET_CAP_MAX and
                    coin['total_volume'] and coin['total_volume'] >= VOLUME_MIN and
                    "meme" in coin['categories']
                ):
                    send_alert(coin)
                else:
                    continue
            except Exception as err:
                print(f"Error parsing coin data: {err}", flush=True)

    except Exception as e:
        print(f"Unexpected error: {e}", flush=True)
        traceback.print_exc()

print("Main loop starting...", flush=True)
while True:
    fetch_snipes()
    time.sleep(SLEEP_TIME)
