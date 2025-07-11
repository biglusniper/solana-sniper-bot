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

BIRDEYE_API_KEY = os.getenv("BIRDEYE_API_KEY")
if not BIRDEYE_API_KEY:
    print("❌ BIRDEYE_API_KEY is missing! Exiting.", flush=True)
    sys.exit(1) # Exit with an error code
print("BIRDEYE_API_KEY loaded ✅", flush=True)

print("DEBUG: Environment variables checked.", flush=True)

# Step 2: Config
MIN_LIQUIDITY = 1000
SLEEP_TIME = 60  # seconds

print(f"DEBUG: Configuration: MIN_LIQUIDITY={MIN_LIQUIDITY}, SLEEP_TIME={SLEEP_TIME} seconds.", flush=True)

def send_alert(token):
    """
    Sends a Discord alert for a detected token.
    """
    message = {
        "content": f"New Token Detected\n"
                   f"Name: {token.get('name', 'N/A')}\n"
                   f"Symbol: {token.get('symbol', 'N/A')}\n"
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
    Fetches trending tokens from Birdeye API and sends alerts for new tokens
    meeting the liquidity criteria.
    """
    print("Step 3: Checking Birdeye trending tokens...", flush=True)

    url = "https://public-api.birdeye.so/defi/token_trending"
    headers = {
        "X-API-KEY": BIRDEYE_API_KEY
    }
    print(f"DEBUG: Birdeye API URL: {url}", flush=True)
    # Print a truncated API key for security, but confirm it's being used
    print(f"DEBUG: Birdeye API Headers (X-API-KEY truncated): X-API-KEY={BIRDEYE_API_KEY[:5]}...", flush=True)

    try:
        # Added a timeout to prevent requests from hanging indefinitely
        res = requests.get(url, headers=headers, timeout=15) # 15-second timeout
        print(f"Status Code: {res.status_code}", flush=True)

        # Print raw response for debugging JSON structure
        # This is CRUCIAL for understanding the actual data format from Birdeye
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
        # If your raw response shows the list directly, change to `tokens = data`.
        # If it's under a different key (e.g., 'trending_tokens'), adjust accordingly.
        tokens = data.get("data", [])

        if not tokens: # Check if the 'data' key returned an empty list or was missing
            print("❗ Birdeye API 'data' key is empty or not found in response. No tokens to process.", flush=True)
            # You might want to print the full 'data' object here for more debugging if this happens
            # print(f"DEBUG: Full data object: {data}", flush=True)
            return
        
        # Ensure 'tokens' is actually a list before proceeding
        if not isinstance(tokens, list):
            print(f"❌ Birdeye API 'data' key did not return a list. Type received: {type(tokens).__name__}. Full data: {data}", flush=True)
            return


        print(f"🔍 Found {len(tokens)} trending tokens...", flush=True)

        # Loop through tokens and process
        # Limiting to top 20 for speed and to reduce Discord spam during testing
        for i, token in enumerate(tokens):
            if i >= 20:
                print("DEBUG: Reached limit of 20 tokens for processing this cycle.", flush=True)
                break

            # Adjust these keys based on the actual Birdeye trending API response for each token object
            # Common keys are 'name', 'symbol', 'address', 'liquidity'.
            # If they are nested (e.g., token['attributes']['liquidity']), you'll need to adjust.
            token_name = token.get('name', 'N/A')
            token_symbol = token.get('symbol', 'N/A')
            token_address = token.get('address', '')
            token_liquidity = token.get('liquidity', 0) # Adjust if key is different

            print(f"DEBUG: Processing token {i+1}: Symbol='{token_symbol}', Name='{token_name}', Address='{token_address}', Liquidity=${token_liquidity:,.0f}", flush=True)

            if token_liquidity > MIN_LIQUIDITY:
                send_alert({
                    'name': token_name,
                    'symbol': token_symbol,
                    'address': token_address,
                    'liquidity': token_liquidity
                })
            else:
                print(f"⏩ Skipping {token_symbol} - liquidity ${token_liquidity:,.0f} is below minimum ${MIN_LIQUIDITY:,.0f}.", flush=True)

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
        check_birdeye()
        print(f"--- Check cycle finished. Sleeping for {SLEEP_TIME} seconds ---", flush=True)
        time.sleep(SLEEP_TIME) # PAUSED FOR THE CONFIGURED TIME - Corrected typo here
except KeyboardInterrupt:
    print("\nScript terminated by user (KeyboardInterrupt). Exiting.", flush=True)
    sys.exit(0)
except Exception as main_loop_e:
    # This catches any errors that escape the check_birdeye function or occur in the loop itself
    print(f"❌ An UNEXPECTED ERROR occurred in the main loop: {type(main_loop_e).__name__}: {main_loop_e}", flush=True)
    traceback.print_exc()
    sys.exit(1) # Exit with an error code
