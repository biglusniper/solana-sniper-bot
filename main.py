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

# BIRDEYE_API_KEY is no longer needed for CoinGecko, but keeping the check
# just in case it's still in the environment and to avoid immediate exit if missing.
# It will simply not be used in the API call.
BIRDEYE_API_KEY = os.getenv("BIRDEYE_API_KEY")
if not BIRDEYE_API_KEY:
    print("❗ BIRDEYE_API_KEY is missing, but not strictly required for CoinGecko. Continuing...", flush=True)
else:
    print("BIRDEYE_API_KEY loaded ✅ (will not be used for CoinGecko API calls)", flush=True)


print("DEBUG: Environment variables checked.", flush=True)

# Step 2: Config
# For CoinGecko trending, we'll use market_cap_rank as a relevance metric.
# A lower rank is better (e.g., rank 1 is the highest).
MAX_MARKET_CAP_RANK = 50 # Only alert for tokens within the top 50 market cap rank
SLEEP_TIME = 60  # seconds

print(f"DEBUG: Configuration: MAX_MARKET_CAP_RANK={MAX_MARKET_CAP_RANK}, SLEEP_TIME={SLEEP_TIME} seconds.", flush=True)

def send_alert(token):
    """
    Sends a Discord alert for a detected token.
    """
    # Adjusted link for CoinGecko, using token_id which is unique to CoinGecko
    message = {
        "content": f"New Token Detected\n"
                   f"Name: {token.get('name', 'N/A')}\n"
                   f"Symbol: {token.get('symbol', 'N/A')}\n"
                   f"Market Cap Rank: {token.get('market_cap_rank', 'N/A')}\n"
                   f"🔗 https://www.coingecko.com/en/coins/{token.get('id', '')}" 
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

def check_coingecko():
    """
    Fetches trending coins from CoinGecko API and sends alerts for coins
    meeting the market cap rank criteria.
    """
    print("Step 3: Checking CoinGecko trending coins...", flush=True)

    # CoinGecko's public trending endpoint. No API key needed for basic access.
    url = "https://api.coingecko.com/api/v3/search/trending"
    headers = {} # No specific headers like User-Agent are typically required here.
    
    print(f"DEBUG: CoinGecko API URL: {url}", flush=True)
    print("DEBUG: No API key required for this CoinGecko endpoint.", flush=True)

    try:
        # Added a timeout to prevent requests from hanging indefinitely
        res = requests.get(url, headers=headers, timeout=15) # 15-second timeout
        print(f"Status Code: {res.status_code}", flush=True)

        # Print raw response for debugging JSON structure
        print(f"CoinGecko API Response (first 1000 chars): {str(res.text)[:1000]}", flush=True)
        if len(res.text) > 1000:
            print("... (response truncated)", flush=True)


        if res.status_code != 200:
            print(f"❌ CoinGecko API error: Status Code {res.status_code}, Response: {res.text}", flush=True)
            return

        data = res.json()

        # CoinGecko's trending endpoint returns a 'coins' key, where each item
        # is a wrapper object containing the actual coin 'item'.
        trending_coins_raw = data.get('coins', []) 

        if not isinstance(trending_coins_raw, list):
            print(f"❌ CoinGecko API response did not return a list of coins. Type received: {type(trending_coins_raw).__name__}. Full data: {data}", flush=True)
            return
        
        if not trending_coins_raw: # Check if the list of coins is empty
            print("❗ CoinGecko API returned an empty list of trending coins. No tokens to process.", flush=True)
            return


        print(f"🔍 Found {len(trending_coins_raw)} trending coins from CoinGecko...", flush=True)

        # Loop through the raw trending items and extract relevant coin info
        for i, trending_coin_wrapper in enumerate(trending_coins_raw):
            if i >= 20: # Limit to top 20 coins for processing
                print("DEBUG: Reached limit of 20 coins for processing this cycle.", flush=True)
                break

            coin_data = trending_coin_wrapper.get('item', {})
            
            token_id = coin_data.get('id', '') # Unique CoinGecko ID for the coin
            token_name = coin_data.get('name', 'N/A')
            token_symbol = coin_data.get('symbol', 'N/A')
            market_cap_rank = coin_data.get('market_cap_rank') # Can be None if not available

            # CoinGecko trending API does not directly provide 'liquidity' or 'address'
            # We'll use market_cap_rank as our filter criteria
            
            print(f"DEBUG: Processing coin {i+1}: ID='{token_id}', Symbol='{token_symbol}', Name='{token_name}', Market Cap Rank={market_cap_rank}", flush=True)

            if market_cap_rank is not None and market_cap_rank <= MAX_MARKET_CAP_RANK:
                send_alert({
                    'id': token_id, # Pass CoinGecko ID for the link
                    'name': token_name,
                    'symbol': token_symbol,
                    'market_cap_rank': market_cap_rank, # Pass rank for the alert
                    'address': '' # Address is not available from this endpoint
                })
            else:
                print(f"⏩ Skipping {token_symbol} - Market Cap Rank {market_cap_rank} is not within top {MAX_MARKET_CAP_RANK}.", flush=True)

    except requests.exceptions.Timeout as e:
        print(f"❌ CoinGecko API request timed out after {res.request.timeout} seconds: {e}", flush=True)
        traceback.print_exc()
    except requests.exceptions.ConnectionError as e:
        print(f"❌ CoinGecko API connection error (e.g., DNS failure, refused connection): {e}", flush=True)
        traceback.print_exc()
    except requests.exceptions.RequestException as req_err:
        # Catches any other requests-related errors (e.g., HTTPError for 4xx/5xx responses)
        print(f"❌ General Request error in CoinGecko fetch: {type(req_err).__name__}: {req_err}", flush=True)
        traceback.print_exc()
    except ValueError as json_err:
        # This catches errors if res.json() fails to parse the response (e.g., not valid JSON)
        print(f"❌ JSON decoding error from CoinGecko response: {json_err}. Full Response text: {res.text if 'res' in locals() else 'No response received'}", flush=True)
        traceback.print_exc()
    except Exception as e:
        # Catch any other unexpected errors that were not specifically handled above
        print(f"❌ An UNEXPECTED ERROR occurred in check_coingecko: {type(e).__name__}: {e}", flush=True)
        traceback.print_exc() # Print full traceback for unexpected errors

# Main loop
print("DEBUG: Entering main loop.", flush=True)
try:
    while True:
        print("\n--- Starting new check cycle ---", flush=True) # Clearly mark cycles in logs
        check_coingecko() # Changed to call the CoinGecko function
        print(f"--- Check cycle finished. Sleeping for {SLEEP_TIME} seconds ---", flush=True) 
        time.sleep(SLEEP_TIME) # Pause for the configured time
except KeyboardInterrupt:
    print("\nScript terminated by user (KeyboardInterrupt). Exiting.", flush=True)
    sys.exit(0)
except Exception as main_loop_e:
    # This catches any errors that escape the check_coingecko function or occur in the loop itself
    print(f"❌ An UNEXPECTED ERROR occurred in the main loop: {type(main_loop_e).__name__}: {main_loop_e}", flush=True)
    traceback.print_exc()
    sys.exit(1) # Exit with an error code
