import requests
import time
import os
import sys
import traceback # Import traceback for detailed error printing

# Force immediate flush for all print statements to ensure logs appear promptly
# This helps prevent buffering issues on platforms like Render.
if sys.version_info >= (3, 7):
    sys.stdout.reconfigure(line_buffering=True)

print("DEBUG: Script execution started.", flush=True)

# Step 1: Load environment variables
print("Step 1: Bot starting...", flush=True)

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
if not DISCORD_WEBHOOK_URL:
    print("❌ DISCORD_WEBHOOK_URL is missing! Exiting.", flush=True)
    sys.exit(1) # Exit with an error code
print("DISCORD_WEBHOOK_URL loaded ✅", flush=True)

# --- IMPORTANT: API Key directly embedded as requested ---
# It is generally recommended to use environment variables for API keys for security.
# Example: BIRDEYE_API_KEY = os.getenv("BIRDEYE_API_KEY")
BIRDEYE_API_KEY = "264eb2443d724f85b4ec3f125bb7b8b1" # Your Birdeye API Key
print("BIRDEYE_API_KEY loaded ✅ (directly from script)", flush=True)


print("DEBUG: Environment variables checked.", flush=True)

# Step 2: Config
# Define the specific coins we are interested in by their name or symbol from Birdeye
# IMPORTANT: Verify the exact 'name' and 'symbol' as they appear in Birdeye's API response
# for "Degecoin" and "Unicorn Fart Dust" to ensure accurate filtering.
TARGET_COINS = [
    {"name_match": "Degecoin", "symbol_match": "DEGE"}, # Placeholder, confirm exact name/symbol on Birdeye
    {"name_match": "Unicorn Fart Dust", "symbol_match": "UFD"}
]
MIN_LIQUIDITY = 1000 # Only alert for tokens with liquidity above this value
SLEEP_TIME = 300  # seconds (Increased to 5 minutes to avoid rate limit issues)

print(f"DEBUG: Configuration: Targeting specific coins: {TARGET_COINS}, MIN_LIQUIDITY={MIN_LIQUIDITY}, SLEEP_TIME={SLEEP_TIME} seconds.", flush=True)

def send_alert(token):
    """
    Sends a Discord alert for a detected token.
    """
    # Adjusted message content to be more specific for targeted coin alerts
    message = {
        "content": f"🎯 Targeted Coin Alert! 🎯\n"
                   f"Coin: {token.get('name', 'N/A')} ({token.get('symbol', 'N/A')})\n"
                   f"Liquidity: ${token.get('liquidity', 0):,.0f}\n"
                   f"🔗 https://birdeye.so/token/{token.get('address', '')}"
    }

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=message)
        if response.status_code != 204: # Discord webhook returns 204 No Content on success
            print(f"❌ Discord webhook error: Status Code {response.status_code}, Response: {response.text}", flush=True)
        else:
            print(f"✅ Sent alert for {token.get('symbol', 'N/A')}", flush=True)
    except Exception as e:
        print(f"❌ Failed to send Discord alert: {type(e).__name__}: {e}", flush=True)
        traceback.print_exc() # Print full traceback for debugging

def check_birdeye():
    """
    Fetches trending tokens from Birdeye API and sends alerts for specific
    target coins meeting the liquidity criteria.
    """
    print("Step 3: Checking Birdeye trending tokens for specific targets...", flush=True)

    url = "https://public-api.birdeye.so/defi/token_trending"
    headers = {
        "X-API-KEY": BIRDEYE_API_KEY # Using the Birdeye API key
    }
    print(f"DEBUG: Birdeye API URL: {url}", flush=True)
    # Print a truncated API key for security, but confirm it's being used
    print(f"DEBUG: Birdeye API Headers (X-API-KEY truncated): X-API-KEY={BIRDEYE_API_KEY[:5]}...", flush=True)

    try:
        # Added a timeout to prevent requests from hanging indefinitely
        res = requests.get(url, headers=headers, timeout=15) # 15-second timeout
        print(f"Status Code: {res.status_code}", flush=True)

        # Print raw response for debugging JSON structure
        print(f"Birdeye API Response (first 1000 chars): {str(res.text)[:1000]}", flush=True)
        if len(res.text) > 1000:
            print("... (response truncated)", flush=True)


        if res.status_code != 200:
            print(f"❌ Birdeye API error: Status Code {res.status_code}, Response: {res.text}", flush=True)
            return

        data = res.json()

        # Check the 'success' flag commonly present in API responses
        if not data.get("success"):
            print(f"❌ Birdeye API returned success: false. Message: {data.get('message', 'No message provided')}", flush=True)
            return

        # --- IMPORTANT: Adjust 'data.get("data", [])' based on actual API response structure! ---
        # Based on typical Birdeye responses, trending tokens are often under a 'data' key.
        tokens = data.get("data", [])

        if not isinstance(tokens, list):
            print(f"❌ Birdeye API response did not return a list of tokens. Type received: {type(tokens).__name__}. Full data: {data}", flush=True)
            return

        if not tokens: # Check if the list of coins is empty
            print("❗ Birdeye API returned an empty list of tokens. No tokens to process.", flush=True)
            return


        print(f"🔍 Found {len(tokens)} trending tokens from Birdeye. Filtering for targets...", flush=True)

        found_and_alerted_target_coins = [] # To track which target coins met criteria

        # Loop through the fetched tokens and apply filtering criteria for target names/symbols
        for i, token in enumerate(tokens):
            token_name = token.get('name', 'N/A')
            token_symbol = token.get('symbol', 'N/A')
            token_liquidity = token.get('liquidity', 0) # Adjust if key is different
            token_address = token.get('address', '')

            is_target_coin = False
            for target in TARGET_COINS:
                # Case-insensitive comparison for name and symbol
                if (target["name_match"].lower() == token_name.lower() or
                    target["symbol_match"].lower() == token_symbol.lower()):
                    is_target_coin = True
                    break

            if is_target_coin:
                print(f"DEBUG: Found target coin: Symbol='{token_symbol}', Name='{token_name}', Liquidity=${token_liquidity:,.0f}", flush=True)

                if token_liquidity > MIN_LIQUIDITY:
                    send_alert({
                        'name': token_name,
                        'symbol': token_symbol,
                        'address': token_address,
                        'liquidity': token_liquidity
                    })
                    found_and_alerted_target_coins.append(token_name) # Use name for tracking
                else:
                    print(f"⏩ Skipping {token_symbol} - liquidity ${token_liquidity:,.0f} is below minimum ${MIN_LIQUIDITY:,.0f}.", flush=True)
            else:
                # If it's not a target coin, just print debug info if needed, or skip
                # print(f"DEBUG: Skipping non-target coin: {token_symbol}", flush=True)
                pass # Do nothing for non-target coins

        # Check if all target coins were found in the fetched data
        # This check might be less useful for "trending" endpoint as it's not guaranteed to have all coins
        # but can help debug if a target name/symbol is wrong.
        for target in TARGET_COINS:
            target_found_in_response = False
            for token in tokens:
                if (target["name_match"].lower() == token.get('name', '').lower() or
                    target["symbol_match"].lower() == token.get('symbol', '').lower()):
                    target_found_in_response = True
                    break
            if not target_found_in_response:
                print(f"INFO: Target coin '{target['name_match']}' (or symbol '{target['symbol_match']}') was not found in the fetched Birdeye trending data.", flush=True)


        if not found_and_alerted_target_coins:
            print("INFO: No target coins met the liquidity criteria in this cycle.", flush=True)


    except requests.exceptions.Timeout as e:
        print(f"❌ Birdeye API request timed out after {res.request.timeout} seconds: {e}", flush=True)
        traceback.print_exc()
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Birdeye API connection error (e.g., DNS failure, refused connection): {e}", flush=True)
        traceback.print_exc()
    except requests.exceptions.RequestException as req_err:
        # Catches any other requests-related errors (e.g., HTTPError for 4xx/5xx responses)
        print(f"❌ General Request error in Birdeye fetch: {type(req_err).__name__}: {req_err}", flush=True)
        traceback.print_exc()
    except ValueError as json_err:
        # This catches errors if res.json() fails to parse the response (e.g., not valid JSON)
        print(f"❌ JSON decoding error from Birdeye response: {json_err}. Full Response text: {res.text if 'res' in locals() else 'No response received'}", flush=True)
        traceback.print_exc()
    except Exception as e:
        # Catch any other unexpected errors that were not specifically handled above
        print(f"❌ An UNEXPECTED ERROR occurred in check_birdeye: {type(e).__name__}: {e}", flush=True)
        traceback.print_exc() # Print full traceback for unexpected errors

# Main loop
print("DEBUG: Entering main loop.", flush=True)
try:
    while True:
        print("\n--- Starting new check cycle ---", flush=True) # Clearly mark cycles in logs
        check_birdeye() # Changed to call the Birdeye function
        print(f"--- Check cycle finished. Sleeping for {SLEEP_TIME} seconds ---", flush=True)
        time.sleep(SLEEP_TIME) # Pause for the configured time
except KeyboardInterrupt:
    print("\nScript terminated by user (KeyboardInterrupt). Exiting.", flush=True)
    sys.exit(0)
except Exception as main_loop_e:
    # This catches any errors that escape the check_birdeye function or occur in the loop itself
    print(f"❌ An UNEXPECTED ERROR occurred in the main loop: {type(main_loop_e).__name__}: {main_loop_e}", flush=True)
    traceback.print_exc()
    sys.exit(1) # Exit with an error code
