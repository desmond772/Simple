import asyncio
import json
import os
import ssl
import aiohttp  # Import aiohttp
import logging
from typing import Optional
from dotenv import load_dotenv
# Note: You can remove `from websockets.legacy.client import WebSocketClientProtocol`
# as you'll no longer be using the websockets library.

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
# Add this for more verbose debugging
logging.getLogger('aiohttp.client').setLevel(logging.DEBUG)


# Load environment variables from .env file
load_dotenv()

# --- Connection Details ---
# The WebSocket URL for Pocket Option's Socket.IO server
WEBSOCKET_URL = "wss://api-in.pocketoption.com:8095/socket.io/?EIO=3&transport=websocket"
# Headers for the WebSocket connection
DEFAULT_HEADERS = {
    "Origin": "https://pocketoption.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
}
# Pocket Option SSID from environment variables
SSID_MESSAGE_RAW = os.environ.get('POCKET_OPTION_SSID')

if not SSID_MESSAGE_RAW:
    logging.critical("POCKET_OPTION_SSID environment variable not set. Exiting.")
    exit(1)

def format_session_id(ssid_message: str) -> Optional[str]:
    """
    Extracts and formats the session data for authentication.
    Handles both raw SSID and the full '42["auth",...]' message.
    """
    try:
        if ssid_message.startswith('42["auth",'):
            return ssid_message
        else:
            auth_data = {
                "session": ssid_message,
                "isDemo": 1,
                "uid": 0,
                "platform": 1,
                "isFastHistory": True,
            }
            auth_json = json.dumps(auth_data)
            return f'42["auth",{auth_json}]'
    except Exception as e:
        logging.error(f"Failed to format session ID: {e}")
        return None

async def receive_and_print_messages(websocket, count: int):
    """
    Helper function to receive and print a specific number of messages using aiohttp.
    """
    for _ in range(count):
        message = await websocket.receive()
        if message.type == aiohttp.WSMsgType.TEXT:
            logging.info(f"Initial server message: {message.data}")

async def connect_to_pocket_option_aiohttp():
    """
    Connects to the Pocket Option WebSocket server and authenticates using aiohttp.
    """
    logging.info("Attempting to connect to Pocket Option WebSocket with aiohttp.")
    
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    formatted_ssid = format_session_id(SSID_MESSAGE_RAW)
    if not formatted_ssid:
        return

    try:
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(
                WEBSOCKET_URL,
                ssl=ssl_context,
                headers=DEFAULT_HEADERS, 
                timeout=10, 
                autoping=True,
                autoclose=True,
                heartbeat=30,
            ) as websocket:
                logging.info("Connected to Pocket Option WebSocket.")
                
                # Handshake Phase
                await receive_and_print_messages(websocket, 2)

                # Authentication Phase
                logging.info("Sending authentication message...")
                await websocket.send_str(formatted_ssid)
                logging.info("Authentication message sent.")
                
                async for msg in websocket:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        logging.info(f"Received message: {msg.data}")
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        logging.error(f"WebSocket Error: {websocket.exception()}")
                        break

    except aiohttp.ClientConnectorError as e:
        logging.critical(f"Connection failed: {e}")
    except asyncio.TimeoutError:
        logging.critical("Connection attempt timed out.")
    except Exception:
        logging.exception("An unexpected fatal error occurred:")

if __name__ == "__main__":
    asyncio.run(connect_to_pocket_option_aiohttp())
