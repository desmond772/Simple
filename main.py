import asyncio
import json
import os
import logging
import random
from typing import Optional
from dotenv import load_dotenv
import websockets

# --- Production Readiness Checklist ---
# 1. Use environment variables for sensitive data. (Addressed with .env)
# 2. Implement robust error handling. (Addressed with try/except blocks)
# 3. Use logging, not print. (Addressed with logging module)
# 4. Use a dependency manager and virtual environment. (Manual step: see below)
# 5. Lock dependencies for reproducible builds. (Manual step: see below)
# 6. Separate configuration from code. (Addressed with .env)
# 7. Use a clear entry point. (Addressed with `if __name__ == "__main__":`)

# --- Configure Logging ---
logging.basicConfig(
    level=logging.INFO,  # Set to INFO for production, DEBUG for development
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logging.getLogger('websockets').setLevel(logging.WARNING) # Reduce websockets verbosity

# Load environment variables from .env file
load_dotenv()

# --- Connection Details ---
POCKET_OPTION_SSID = os.getenv("POCKET_OPTION_SSID")
WEBSOCKET_URL = os.getenv("WEBSOCKET_URL")
ORIGIN = os.getenv("ORIGIN")

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:75.0) Gecko/20100101 Firefox/75.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0'
]
USER_AGENT = random.choice(USER_AGENTS)


def main_sync():
    """Synchronous entry point for the application setup."""
    # Ensure all required environment variables are set.
    if not all([WEBSOCKET_URL, ORIGIN, POCKET_OPTION_SSID]):
        logging.critical("Missing one or more required environment variables. Exiting.")
        logging.critical("Please check your .env file and ensure it is in the root directory.")
        exit(1)

    logging.info("Starting bot. All environment variables loaded successfully.")
    asyncio.run(main())

def format_auth_message(ssid: str) -> str:
    """Formats the authentication message for Pocket Option."""
    auth_data = {
        "session": ssid,
        "isDemo": 1,
        "uid": 0,
        "platform": 1,
        "isFastHistory": True,
    }
    auth_json = json.dumps(auth_data, separators=(',', ':'))
    return f'42["auth",{auth_json}]'

async def pocket_option_bot():
    """Main bot logic with enhanced error handling."""
    custom_headers = {
        "User-Agent": USER_AGENT,
        "Origin": ORIGIN,
        "Cookie": f"POSESSION={POCKET_OPTION_SSID}"
    }

    logging.info("Attempting to connect with the following details:")
    logging.debug(f"  URL: {WEBSOCKET_URL}")
    logging.debug(f"  Headers: {{'User-Agent': '{USER_AGENT}', 'Origin': '{ORIGIN}', 'Cookie': 'POSESSION=[sanitized]'}}")

    try:
        async with websockets.connect(
            WEBSOCKET_URL,
            extra_headers=custom_headers,
            ping_interval=20,
            ping_timeout=20,
        ) as ws:
            logging.info("Connected to Pocket Option WebSocket server!")
            
            # Send the authentication message
            auth_message = format_auth_message(POCKET_OPTION_SSID)
            logging.info(f"Sending authentication message...")
            await ws.send(auth_message)
            
            # Main message loop to process incoming data
            async for message in ws:
                logging.debug(f"Received message: {message}")
                # You will add your bot's logic here to process messages
                # and send trading commands based on your strategy.
                
    except websockets.exceptions.InvalidURI as e:
        logging.critical(f"Invalid WebSocket URI: {e}. Please check WEBSOCKET_URL in your .env file.")
        raise  # Propagate error to prevent endless reconnection loop
    except websockets.exceptions.InvalidHandshake as e:
        logging.error(f"Handshake failed: {e}. Check URL, headers, and credentials.")
        raise
    except websockets.exceptions.ConnectionClosed as e:
        logging.error(f"Connection closed by server with code {e.code}: {e.reason}")
        raise
    except asyncio.TimeoutError:
        logging.error("Connection attempt timed out. Check network or VPN.")
        raise
    except Exception as e:
        logging.exception(f"An unexpected error occurred during the bot execution: {e}")
        raise

async def main():
    """Main entry point for the asyncio application with auto-reconnect logic."""
    backoff = 5
    while True:
        try:
            await pocket_option_bot()
        except asyncio.CancelledError:
            logging.info("Bot execution cancelled.")
            break
        except Exception:
            logging.error(f"An error occurred. Retrying in {backoff} seconds...")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60) # Exponential backoff up to 60 seconds
        else:
            backoff = 5 # Reset backoff on successful connection
        
        logging.info("Reconnecting...")

if __name__ == "__main__":
    try:
        main_sync()
    except KeyboardInterrupt:
        logging.info("Bot shut down manually.")
