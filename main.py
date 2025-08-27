import asyncio
import json
import os
import ssl
import websockets
import logging
from typing import Optional
from dotenv import load_dotenv
from websockets.legacy.client import WebSocketClientProtocol

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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

async def connect_to_pocket_option():
    """
    Connects to the Pocket Option WebSocket server and authenticates.
    """
    logging.info("Attempting to connect to Pocket Option WebSocket.")
    
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    formatted_ssid = format_session_id(SSID_MESSAGE_RAW)
    if not formatted_ssid:
        return

    try:
        async with websockets.connect(
            WEBSOCKET_URL,
            ssl=ssl_context,
            # Changed from 'extra_headers' to 'additional_headers' for websockets v11.0+
            extra_headers=DEFAULT_HEADERS, 
            ping_interval=30,
            ping_timeout=30,
            close_timeout=10,
        ) as websocket:
            logging.info("Connected to Pocket Option WebSocket.")
            
            # Handshake Phase
            await receive_and_print_messages(websocket, 2)
            
            # Authentication Phase
            logging.info("Sending authentication message...")
            await websocket.send(formatted_ssid)
            logging.info("Authentication message sent.")
            
            while True:
                response = await websocket.recv()
                logging.info(f"Received message: {response}")

    except websockets.exceptions.ConnectionClosed as e:
        logging.error(f"Connection closed unexpectedly: {e}")
    except Exception as e:
        logging.critical(f"An unexpected fatal error occurred: {e}")

async def receive_and_print_messages(websocket: WebSocketClientProtocol, count: int):
    """
    Helper function to receive and print a specific number of messages.
    """
    for _ in range(count):
        message = await websocket.recv()
        logging.info(f"Initial server message: {message}")

if __name__ == "__main__":
    asyncio.run(connect_to_pocket_option())
