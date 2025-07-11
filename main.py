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
# For CoinGecko market data, we'll filter by market_cap_rank and 1-hour price change.
MAX_MARKET_CAP_RANK = 50  # Only alert for tokens within the top 50 market cap rank
MIN_PRICE_CHANGE_1H = 10.0 # Only alert if price change in last hour is >= 10%
SLEEP_TIME = 120  # seconds (Increased to 2 minutes to avoid 429 errors)

print(f"DEBUG: Configuration: MAX_MARKET_CAP_RANK={MAX_MARKET_CAP_RANK}, MIN_PRICE_CHANGE_1H={MIN_PRICE_CHANGE_1H}%, SLEEP_TIME={SLEEP_TIME} seconds.", flush=True)

def send_alert(token):
    """
    Sends a Discord alert for a detected token.
    """
    # Adjusted message content to include 1-hour price change
    message = {
        "content": f"🚀 Trending Token Alert! 🚀\n"
                   f"Name: {token.get('name', 'N/A')}\n"
                   f"Symbol: {token.get('symbol', 'N/A')}\n"
                   f"Market Cap Rank: {token.get('market_cap_rank', 'N/A')}\n"
                   f"1-Hour Price Change: {token.get('price_change_percentage_1h', 'N/A'):.2f}%\n"
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
    Fetches market data for coins from CoinGecko API and sends alerts for coins
    meeting the market cap rank and 1-hour price change criteria.
    """
    print("Step 3: Checking CoinGecko market data for top coins with 1-hour change...", flush=True)

    # CoinGecko's /coins/markets endpoint for detailed market data, including price changes.
    # We request data for USD, sort by market cap, and include 1-hour price change.
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc", # Sort by market cap descending
        "per_page": 100, # Fetch enough coins to cover top 50, plus some buffer
        "page": 1,
        "price_change_percentage": "1h", # Request 1-hour price change
        "sparkline": "false" # Not needed for this bot
    }
    headers = {} # No specific headers like User-Agent are typically required here.
    
    print(f"DEBUG: CoinGecko API URL: {url} with params: {params}", flush=True)
    print("DEBUG: No API key required for this CoinGecko endpoint (for basic usage).", flush=True)

    try:
        # Added a timeout to prevent requests from hanging indefinitely
        res = requests.get(url, headers=headers, params=params, timeout=15) # Pass params here
        print(f"Status Code: {res.status_code}", flush=True)

        # Print raw response for debugging JSON structure
        print(f"CoinGecko API Response (first 1000 chars): {str(res.text)[:1000]}", flush=True)
        if len(res.text) > 1000:
            print("... (response truncated)", flush=True)


        if res.status_code != 200:
            print(f"❌ CoinGecko API error: Status Code {res.status_code}, Response: {res.text}", flush=True)
            return

        coins_data = res.json()

        if not isinstance(coins_data, list):
            print(f"❌ CoinGecko API response did not return a list of coins. Type received: {type(coins_data).__name__}. Full data: {data}", flush=True)
            return
        
        if not coins_data: # Check if the list of coins is empty
            print("❗ CoinGecko API returned an empty list of coins. No tokens to process.", flush=True)
            return


        print(f"🔍 Found {len(coins_data)} coins from CoinGecko market data...", flush=True)

        # Loop through the coins and apply filtering criteria
        processed_count = 0
        for coin in coins_data:
            # We already sorted by market_cap_desc and fetched enough, so just check rank
            market_cap_rank = coin.get('market_cap_rank') 
            price_change_1h = coin.get('price_change_percentage_1h_in_currency')

            token_id = coin.get('id', '')
            token_name = coin.get('name', 'N/A')
            token_symbol = coin.get('symbol', 'N/A')
            
            print(f"DEBUG: Processing coin: Symbol='{token_symbol}', Rank={market_cap_rank}, 1h Change={price_change_1h:.2f}%" if price_change_1h is not None else f"DEBUG: Processing coin: Symbol='{token_symbol}', Rank={market_cap_rank}, 1h Change=N/A", flush=True)

            # Filter: must be within MAX_MARKET_CAP_RANK AND have a significant 1-hour price increase
            if (market_cap_rank is not None and market_cap_rank <= MAX_MARKET_CAP_RANK and
                price_change_1h is not None and price_change_1h >= MIN_PRICE_CHANGE_1H):
                
                send_alert({
                    'id': token_id, 
                    'name': token_name,
                    'symbol': token_symbol,
                    'market_cap_rank': market_cap_rank, 
                    'price_change_percentage_1h': price_change_1h # Pass 1h change for alert
                })
                processed_count += 1
            else:
                print(f"⏩ Skipping {token_symbol} - Does not meet rank (<= {MAX_MARKET_CAP_RANK}) or 1h change (>= {MIN_PRICE_CHANGE_1H}%) criteria.", flush=True)

            if processed_count >= 20: # Limit alerts to 20 per cycle to prevent spam
                print("DEBUG: Reached limit of 20 alerts for this cycle.", flush=True)
                break


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
