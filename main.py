import requests
import time
import os

print("DEBUG: Script execution started.") # Debug print

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

print("DEBUG: Environment variables checked.") # Debug print

# Step 2: Config
MIN_LIQUIDITY = 1000
SLEEP_TIME = 60  # seconds
print(f"DEBUG: Configuration: MIN_LIQUIDITY={MIN_LIQUIDITY}, SLEEP_TIME={SLEEP_TIME}") # Debug print

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
            print(f"❌ Discord webhook error: {response.status_code} - {response.text}")
        else:
            print(f"✅ Sent alert for {token.get('symbol', 'N/A')}")
    except Exception as e:
        print(f"❌ Failed to send Discord alert: {e}")

def check_birdeye():
    print("Step 3: Checking Birdeye trending tokens...") # Updated message

    url = "https://public-api.birdeye.so/defi/token_trending"
    headers = {
        "X-API-KEY": BIRDEYE_API_KEY
    }
    print(f"DEBUG: Birdeye API URL: {url}") # Debug print
    print(f"DEBUG: Birdeye API Headers (X-API-KEY truncated): X-API-KEY={BIRDEYE_API_KEY[:5]}...") # Debug print

    try:
        res = requests.get(url, headers=headers, timeout=10) # Added a timeout for safety
        print("Status Code:", res.status_code)

        # Print raw response for debugging - KEEP THIS FOR NOW
        print("Birdeye API Response (first 1000 chars):", str(res.text)[:1000])

        if res.status_code != 200:
            print(f"❌ Birdeye API error: {res.status_code} - {res.text}")
            return

        data = res.json()
        if not data.get("success"):
            print(f"❌ Birdeye API returned success: false. Message: {data.get('message', 'No message provided')}")
            return

        # <<< IMPORTANT: Adjust 'data.get("data", [])' based on actual API response structure! >>>
        tokens = data.get("data", [])
        if not tokens: # Check if the 'data' key returned an empty list
            print("❗ Birdeye API 'data' key is empty or not found.")
            # If the tokens are at the root, try: tokens = data if isinstance(data, list) else []
            # Or if they are under a different key, e.g., 'trending_items': tokens = data.get('trending_items', [])
            return

        print(f"🔍 Found {len(tokens)} trending tokens...")

        # Loop through tokens and process
        for i, token in enumerate(tokens):
            if i >= 20: # Limit to top 20 for initial testing
                print("DEBUG: Reached limit of 20 tokens for processing.")
                break

            # Adjust these keys based on the actual Birdeye trending API response for each token object
            token_name = token.get('name', 'N/A')
            token_symbol = token.get('symbol', 'N/A')
            token_address = token.get('address', '')
            token_liquidity = token.get('liquidity', 0) # Adjust if key is different
            print(f"DEBUG: Processing token: Symbol={token_symbol}, Liquidity={token_liquidity}")

            if token_liquidity > MIN_LIQUIDITY:
                send_alert({
                    'name': token_name,
                    'symbol': token_symbol,
                    'address': token_address,
                    'liquidity': token_liquidity
                })
            else:
                print(f"⏩ Skipping {token_symbol} - liquidity ${token_liquidity:,.0f}")

    except requests.exceptions.Timeout as e:
        print(f"❌ Birdeye API request timed out: {e}")
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Birdeye API connection error: {e}")
    except requests.exceptions.RequestException as req_err:
        print(f"❌ General Request error in Birdeye fetch: {req_err}")
    except ValueError as json_err:
        # This catches errors if res.json() fails to parse the response
        print(f"❌ JSON decoding error from Birdeye response: {json_err}. Full Response text: {res.text if 'res' in locals() else 'No response'}")
    except Exception as e:
        # Catch any other unexpected errors
        print(f"❌ An UNEXPECTED ERROR occurred in check_birdeye: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc() # Print full traceback for unexpected errors

# Main loop
print("DEBUG: Entering main loop.") # Debug print
try:
    while True:
        print("\n--- Starting new check cycle ---") # Clearly mark cycles
        check_birdeye()
        print(f"--- Check cycle finished. Sleeping for {SLEEP_TIME} seconds ---") # Debug print
        time.sleep(SLEEP_TIME)
except Exception as main_loop_e:
    print(f"❌ An UNEXPECTED ERROR occurred in the main loop: {type(main_loop_e).__name__}: {main_loop_e}")
    import traceback
    traceback.print_exc()
