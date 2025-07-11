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

# BIRDEYE_API_KEY is no longer needed for Dexscreener, but keeping the check
# just in case it's still in the environment and to avoid immediate exit if missing.
# It will simply not be used in the API call.
BIRDEYE_API_KEY = os.getenv("BIRDEYE_API_KEY")
if not BIRDEYE_API_KEY:
    print("❗ BIRDEYE_API_KEY is missing, but not strictly required for Dexscreener. Continuing...", flush=True)
else:
    print("BIRDEYE_API_KEY loaded ✅ (will not be used for Dexscreener API calls)", flush=True)


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
                   f"🔗 https://dexscreener.com/solana/{token.get('address', '')}" # Adjusted link for Dexscreener
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

def check_dexscreener():
    """
    Fetches pairs from Dexscreener API and sends alerts for new tokens
    meeting the liquidity criteria.
    """
    print("Step 3: Checking Dexscreener pairs...", flush=True)

    # Using Dexscreener's /latest/dex/pairs endpoint.
    # This endpoint allows filtering by chain and is more commonly used for data retrieval.
    # We'll fetch pairs for Solana.
    url = "https://api.dexscreener.com/latest/dex/pairs/solana" # Specify chain
    
    # Adding a User-Agent header to make the request look more like a browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    print(f"DEBUG: Dexscreener API URL: {url}", flush=True)
    print("DEBUG: No API key required for this Dexscreener endpoint.", flush=True)
    print("DEBUG: Using User-Agent header to mimic browser request.", flush=True)

    try:
        # Added a timeout to prevent requests from hanging indefinitely
        res = requests.get(url, headers=headers, timeout=15) # 15-second timeout
        print(f"Status Code: {res.status_code}", flush=True)

        # Print raw response for debugging JSON structure
        print(f"Dexscreener API Response (first 1000 chars): {str(res.text)[:1000]}", flush=True)
        if len(res.text) > 1000:
            print("... (response truncated)", flush=True)


        if res.status_code != 200:
            print(f"❌ Dexscreener API error: Status Code {res.status_code}, Response: {res.text}", flush=True)
            return

        data = res.json()

        # Dexscreener /pairs endpoint usually returns a 'pairs' key containing a list of pair objects.
        pairs = data.get('pairs', []) 

        if not isinstance(pairs, list):
            print(f"❌ Dexscreener API response did not return a list of pairs. Type received: {type(pairs).__name__}. Full data: {data}", flush=True)
            return
        
        if not pairs: # Check if the list of pairs is empty
            print("❗ Dexscreener API returned an empty list of pairs. No tokens to process.", flush=True)
            return


        print(f"🔍 Found {len(pairs)} pairs from Dexscreener...", flush=True)

        # Loop through pairs and extract token info.
        # A pair typically has baseToken and quoteToken. We're interested in the baseToken.
        for i, pair in enumerate(pairs):
            if i >= 20: # Limit to top 20 pairs for processing
                print("DEBUG: Reached limit of 20 pairs for processing this cycle.", flush=True)
                break

            base_token_info = pair.get('baseToken', {})
            token_name = base_token_info.get('name', 'N/A')
            token_symbol = base_token_info.get('symbol', 'N/A')
            token_address = base_token_info.get('address', '') # Base token's contract address

            # Liquidity for the pair is usually directly under the pair object
            liquidity_info = pair.get('liquidity', {})
            token_liquidity = liquidity_info.get('usd', 0) # Get USD liquidity

            print(f"DEBUG: Processing pair {i+1}: Base Symbol='{token_symbol}', Name='{token_name}', Address='{token_address}', Liquidity=${token_liquidity:,.0f}", flush=True)

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
        print(f"❌ Dexscreener API request timed out after {res.request.timeout} seconds: {e}", flush=True)
        traceback.print_exc()
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Dexscreener API connection error (e.g., DNS failure, refused connection): {e}", flush=True)
        traceback.print_exc()
    except requests.exceptions.RequestException as req_err:
        # Catches any other requests-related errors (e.g., HTTPError for 4xx/5xx responses)
        print(f"❌ General Request error in Dexscreener fetch: {type(req_err).__name__}: {req_err}", flush=True)
        traceback.print_exc()
    except ValueError as json_err:
        # This catches errors if res.json() fails to parse the response (e.g., not valid JSON)
        print(f"❌ JSON decoding error from Dexscreener response: {json_err}. Full Response text: {res.text if 'res' in locals() else 'No response received'}", flush=True)
        traceback.print_exc()
    except Exception as e:
        # Catch any other unexpected errors that were not specifically handled above
        print(f"❌ An UNEXPECTED ERROR occurred in check_dexscreener: {type(e).__name__}: {e}", flush=True)
        traceback.print_exc() # Print full traceback for unexpected errors

# Main loop
print("DEBUG: Entering main loop.", flush=True)
try:
    while True:
        print("\n--- Starting new check cycle ---", flush=True) # Clearly mark cycles in logs
        check_dexscreener() # Changed to call the Dexscreener function
        # Corrected typo from SLEEP_LIQUIDITY to SLEEP_TIME
        print(f"--- Check cycle finished. Sleeping for {SLEEP_TIME} seconds ---", flush=True) 
        time.sleep(SLEEP_TIME) # Pause for the configured time
except KeyboardInterrupt:
    print("\nScript terminated by user (KeyboardInterrupt). Exiting.", flush=True)
    sys.exit(0)
except Exception as main_loop_e:
    # This catches any errors that escape the check_dexscreener function or occur in the loop itself
    print(f"❌ An UNEXPECTED ERROR occurred in the main loop: {type(main_loop_e).__name__}: {main_loop_e}", flush=True)
    traceback.print_exc()
    sys.exit(1) # Exit with an error code
