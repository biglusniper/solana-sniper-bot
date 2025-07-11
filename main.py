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
    Fetches trending/top tokens from Dexscreener API and sends alerts for new tokens
    meeting the liquidity criteria.
    """
    print("Step 3: Checking Dexscreener top boosted tokens...", flush=True)

    # Using Dexscreener's top boosted tokens endpoint as an example.
    # This endpoint generally does NOT require an API key.
    url = "https://api.dexscreener.com/latest/dex/token-boosts/top/v1"
    
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
        # This is CRUCIAL for understanding the actual data format from Dexscreener
        print(f"Dexscreener API Response (first 1000 chars): {str(res.text)[:1000]}", flush=True)
        if len(res.text) > 1000:
            print("... (response truncated)", flush=True)


        if res.status_code != 200:
            print(f"❌ Dexscreener API error: Status Code {res.status_code}, Response: {res.text}", flush=True)
            return

        data = res.json()

        # Dexscreener's 'token-boosts' endpoint returns a list of token objects directly
        # or sometimes under a key like 'tokens' or 'data'.
        # We'll assume it's a list of tokens at the root or under 'tokens' key.
        tokens = data.get('tokens', data) # Try 'tokens' key, fallback to root if it's a direct list

        if not isinstance(tokens, list):
            print(f"❌ Dexscreener API response did not return a list of tokens. Type received: {type(tokens).__name__}. Full data: {data}", flush=True)
            return
        
        if not tokens: # Check if the list of tokens is empty
            print("❗ Dexscreener API returned an empty list of tokens. No tokens to process.", flush=True)
            return


        print(f"🔍 Found {len(tokens)} top boosted tokens from Dexscreener...", flush=True)

        # Loop through tokens and process
        # Limiting to top 20 for speed and to reduce Discord spam during testing
        for i, token in enumerate(tokens):
            if i >= 20:
                print("DEBUG: Reached limit of 20 tokens for processing this cycle.", flush=True)
                break

            # Adjust these keys based on the actual Dexscreener API response for each token object
            # Common keys for boosted tokens might be 'tokenAddress', 'baseToken.symbol', 'baseToken.name', 'liquidity.usd'
            # Let's try to extract common fields. You might need to refine these based on the actual response.
            token_address = token.get('tokenAddress', '')
            
            # Dexscreener often nests token details, e.g., 'baseToken' object
            # For simplicity, we'll try to get directly, but be prepared to adjust.
            # If the token object itself has 'symbol' and 'name':
            token_symbol = token.get('symbol', 'N/A')
            token_name = token.get('name', 'N/A')

            # Liquidity on Dexscreener is often nested or part of a pair, e.g., 'liquidity.usd'
            # For 'token-boosts/top', it might be directly available or part of a 'pair' object.
            # We'll try to get a 'liquidity' value directly or from a nested 'usd' key.
            # You will need to inspect the actual response to get the correct path to liquidity.
            token_liquidity = token.get('liquidity', 0)
            if isinstance(token_liquidity, dict): # If liquidity is an object like {'usd': 1234.5}
                token_liquidity = token_liquidity.get('usd', 0)


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
        print(f"--- Check cycle finished. Sleeping for {SLEEP_LIQUIDITY} seconds ---", flush=True)
        time.sleep(SLEEP_TIME) # Pause for the configured time
except KeyboardInterrupt:
    print("\nScript terminated by user (KeyboardInterrupt). Exiting.", flush=True)
    sys.exit(0)
except Exception as main_loop_e:
    # This catches any errors that escape the check_dexscreener function or occur in the loop itself
    print(f"❌ An UNEXPECTED ERROR occurred in the main loop: {type(main_loop_e).__name__}: {main_loop_e}", flush=True)
    traceback.print_exc()
    sys.exit(1) # Exit with an error code
