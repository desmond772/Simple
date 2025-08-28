import asyncio
import json
import os
import logging
from typing import Optional
from dotenv import load_dotenv
import socketio

# --- Configure Logging ---
# Set the root logger to DEBUG to catch everything
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
# Add specific loggers for socketio and engineio for detailed handshake info
logging.getLogger('socketio').setLevel(logging.DEBUG)
logging.getLogger('engineio').setLevel(logging.DEBUG)

# Load environment variables from .env file
load_dotenv()

# --- Connection Details ---
# Use the standard HTTPS port (443), which is the default for wss://
# This was identified by inspecting the Pocket Option website.
WEBSOCKET_URL = "https://api-in.pocketoption.com" 
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
            # Use separators to create compact JSON with no spaces
            auth_json = json.dumps(auth_data, separators=(',', ':'))
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
    request_timeout=30 # Keep the timeout at 30 seconds for now
)

@sio.event
async def connect():
    logging.info("Connected to Pocket Option WebSocket server!")
    # Once connected, send the authentication message
    formatted_ssid = format_session_id(SSID_MESSAGE_RAW)
    if formatted_ssid:
        logging.info("Sending authentication message...")
        await sio.send(formatted_ssid)
    else:
        logging.error("Failed to format SSID. Disconnecting.")
        await sio.disconnect()

@sio.event
async def connect_error(data):
    logging.error(f"The connection failed! Reason: {data}")

@sio.event
def disconnect():
    logging.info("Disconnected from Pocket Option WebSocket server.")

@sio.on('*') # Listen for all events
def catch_all_events(event, data):
    logging.info(f"Received event '{event}': {data}")

async def main():
    try:
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
