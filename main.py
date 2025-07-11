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

BIRDEYE_API_KEY = os.getenv("BIRDEYE_API_KEY")
if not BIRDEYE_API_KEY:
    print("❌ BIRDEYE_API_KEY is missing")
    exit()
print("BIRDEYE_API_KEY loaded ✅")

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
    print("Step 3: Checking Birdeye trending tokens...") # Updated message

    url = "https://public-api.birdeye.so/defi/token_trending"
    headers = {
        "X-API-KEY": BIRDEYE_API_KEY
    }

    # You might want to add query parameters based on the documentation for
    # sorting, limiting, or specifying a chain if the trending endpoint supports it.
    # For example:
    # params = {
    #     "chain": "solana", # Verify if this parameter is needed for trending
    #     "sort_by": "volume",
    #     "sort_type": "desc",
    #     "limit": 50
    # }

    try:
        # If you add params, change to: res = requests.get(url, headers=headers, params=params)
        res = requests.get(url, headers=headers)
        print("Status Code:", res.status_code)

        if res.status_code != 200:
            print("❌ Birdeye API error:", res.status_code, res.text)
            return

        # The structure of the response might be different for the trending endpoint.
        # It's common for API responses to wrap data in a "data" key, but always verify.
        data = res.json()
        if not data.get("success"):
            print(f"❌ Birdeye API returned success: false. Message: {data.get('message', 'No message provided')}")
            return

        tokens = data.get("data", []) # Assume the trending tokens are under 'data' key
        print(f"🔍 Found {len(tokens)} trending tokens...")

        # You might need to adjust how you access token properties
        # based on the response structure of the /defi/token_trending endpoint.
        # For example, "liquidity" might be nested or named differently.
        for token in tokens:
            # Placeholder for potential renaming of keys if different in trending API
            token_name = token.get('name', 'N/A')
            token_symbol = token.get('symbol', 'N/A')
            token_address = token.get('address', '')
            token_liquidity = token.get('liquidity', 0) # Adjust if key is different

            if token_liquidity > MIN_LIQUIDITY:
                # You might need to reconstruct the 'token' dictionary
                # if the trending endpoint returns fewer details or different keys
                send_alert({
                    'name': token_name,
                    'symbol': token_symbol,
                    'address': token_address,
                    'liquidity': token_liquidity
                })
            else:
                print(f"⏩ Skipping {token_symbol} - liquidity ${token_liquidity:,.0f}")

    except requests.exceptions.RequestException as req_err:
        print(f"❌ Request error in Birdeye fetch: {req_err}")
    except ValueError as json_err:
        print(f"❌ JSON decoding error from Birdeye response: {json_err}. Response text: {res.text if 'res' in locals() else 'No response'}")
    except Exception as e:
        print(f"❌ An unexpected error occurred in Birdeye fetch: {e}")

# Main loop
while True:
    check_birdeye()
    time.sleep(SLEEP_TIME)
