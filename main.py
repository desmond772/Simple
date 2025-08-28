import asyncio
import json
import os
import logging
from typing import Optional
from dotenv import load_dotenv
import socketio

# --- Configure Logging ---
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logging.getLogger('socketio').setLevel(logging.DEBUG)
logging.getLogger('engineio').setLevel(logging.DEBUG)

# Load environment variables from .env file
load_dotenv()

# --- Connection Details ---
# Pocket Option uses a specific Socket.IO endpoint.
# The URL must include the /socket.io/ path and the query parameters.
# Community-observed details often point to EIO=3, but if it fails,
# you can experiment with EIO=4 or newer.
WEBSOCKET_URL = "wss://api-in.pocketoption.com:8095/socket.io/?EIO=3&transport=websocket" 
SSID_MESSAGE_RAW = os.environ.get('POCKET_OPTION_SSID')

if not SSID_MESSAGE_RAW:
    logging.critical("POCKET_OPTION_SSID environment variable not set. Exiting.")
    exit(1)

def format_session_id(ssid_message: str) -> Optional[str]:
    """
    Formats the session data for authentication.
    Handles both raw SSID and the full '42["auth",...]' message.
    """
    try:
        # A valid full auth message will start with '42["auth",...]'.
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
            # Use separators to create compact JSON with no spaces
            auth_json = json.dumps(auth_data, separators=(',', ':'))
            # This is the correct format for the auth message after connection.
            return f'42["auth",{auth_json}]'
    except Exception as e:
        logging.error(f"Failed to format session ID: {e}")
        return None

# Create a Socket.IO client instance
sio = socketio.AsyncClient(
    logger=True,
    engineio_logger=True,
    reconnection=True,
    reconnection_delay=1,
    reconnection_delay_max=30,
    request_timeout=30
)

@sio.event
async def connect():
    logging.info("Connected to Pocket Option WebSocket server!")
    formatted_ssid = format_session_id(SSID_MESSAGE_RAW)
    if formatted_ssid:
        logging.info("Sending authentication message...")
        # A simple `send` call might not be enough. Using `emit` is often safer.
        await sio.emit('auth', formatted_ssid)
        # For simplicity, using `sio.send()` directly as in your original code
        # might still work, but `sio.emit()` is the standard way to send events.
    else:
        logging.error("Failed to format SSID. Disconnecting.")
        await sio.disconnect()

@sio.event
async def connect_error(data):
    logging.error(f"The connection failed! Reason: {data}")

@sio.event
def disconnect():
    logging.info("Disconnected from Pocket Option WebSocket server.")

@sio.on('*')
def catch_all_events(event, data):
    # This is a good way to debug. You should see a lot of data here if
    # the authentication is successful.
    logging.info(f"Received event '{event}': {data}")

async def main():
    try:
        logging.info(f"Attempting to connect to {WEBSOCKET_URL}...")
        await sio.connect(
            WEBSOCKET_URL,
            transports=['websocket']
        )
        logging.info("Socket.IO client started. Waiting for connection...")
        await sio.wait()
    except asyncio.TimeoutError:
        logging.critical("Connection wait timed out. Check network, VPN, or SSID.")
    except Exception as e:
        logging.exception(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
