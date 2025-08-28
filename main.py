import asyncio
import json
import os
import logging
from typing import Optional
from dotenv import load_dotenv
import websockets

# --- Configure Logging ---
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logging.getLogger('websockets').setLevel(logging.DEBUG)

# Load environment variables from .env file
load_dotenv()

# --- Connection Details ---
# Load credentials and headers from environment variables
WEBSOCKET_URL = os.environ.get('WEBSOCKET_URL')
USER_AGENT = os.environ.get('USER_AGENT')
ORIGIN = os.environ.get('ORIGIN')
POSESSION_COOKIE = os.environ.get('POCKET_OPTION_SSID')

# Ensure all credentials are set
if not all([WEBSOCKET_URL, USER_AGENT, ORIGIN, POSESSION_COOKIE]):
    logging.critical("Missing one or more required environment variables. Exiting.")
    exit(1)

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
        "Cookie": f"POSESSION={POSESSION_COOKIE}"
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
            auth_message = format_auth_message(POSESSION_COOKIE)
            logging.info(f"Sending authentication message: {auth_message}")
            await ws.send(auth_message)
            
            # Main message loop to process incoming data
            async for message in ws:
                logging.debug(f"Received message: {message}")
                # You will add your bot's logic here to process messages
                # and send trading commands based on your strategy.
                
    except websockets.exceptions.InvalidURI as e:
        logging.critical(f"Invalid WebSocket URI: {e}. Please check WEBSOCKET_URL in your .env file.")
    except websockets.exceptions.InvalidHandshake as e:
        logging.error(f"Handshake failed: {e}. Check URL, headers, and credentials.")
    except websockets.exceptions.ConnectionClosed as e:
        logging.error(f"Connection closed by server with code {e.code}: {e.reason}")
    except asyncio.TimeoutError:
        logging.error("Connection attempt timed out. Check network or VPN.")
    except Exception as e:
        logging.exception(f"An unexpected error occurred during the bot execution: {e}")

async def main():
    """Main entry point for the asyncio application with auto-reconnect logic."""
    while True:
        try:
            await pocket_option_bot()
        except asyncio.CancelledError:
            logging.info("Bot execution cancelled.")
            break
        except Exception:
            logging.error("An error occurred. Retrying in 30 seconds...")
            await asyncio.sleep(30)
        
        logging.info("Reconnecting in 5 seconds...")
        await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot shut down manually.")

