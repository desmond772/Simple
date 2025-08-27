import asyncio
import json
import os
import logging
from dotenv import load_dotenv
import socketio

# --- Configure Logging ---
logging.basicConfig(
    level=logging.INFO, # Changed to INFO for cleaner output
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logging.getLogger('socketio').setLevel(logging.INFO)
logging.getLogger('engineio').setLevel(logging.INFO)

# Load environment variables from .env file
load_dotenv()

# --- Connection Details ---
WEBSOCKET_URL = "https://api-in.pocketoption.com:8095" # socketio client needs the base URL
SSID_MESSAGE_RAW = os.environ.get('POCKET_OPTION_SSID')

if not SSID_MESSAGE_RAW:
    logging.critical("POCKET_OPTION_SSID environment variable not set. Exiting.")
    exit(1)

def format_session_id(ssid_message: str) -> str:
    """
    Formats the session data for authentication.
    """
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
        auth_json = json.dumps(auth_data, separators=(',', ':'))
        return f'42["auth",{auth_json}]'

# Create a Socket.IO client instance
sio = socketio.AsyncClient(
    logger=True,
    engineio_logger=True,
    reconnection=True,
    reconnection_delay=1,
    reconnection_delay_max=30
)

@sio.event
async def connect():
    logging.info("Connected to Pocket Option WebSocket server!")
    # Once connected, send the authentication message
    formatted_ssid = format_session_id(SSID_MESSAGE_RAW)
    logging.info("Sending authentication message...")
    await sio.send(formatted_ssid)

@sio.event
def disconnect():
    logging.info("Disconnected from Pocket Option WebSocket server.")

@sio.on('*') # Listen for all events
def catch_all_events(event, data):
    logging.info(f"Received event '{event}': {data}")

async def main():
    try:
        await sio.connect(WEBSOCKET_URL, transports=['websocket'])
        logging.info("Socket.IO client started. Waiting for connection...")
        await sio.wait()
    except Exception as e:
        logging.critical(f"An error occurred during connection: {e}")

if __name__ == "__main__":
    asyncio.run(main())
        
