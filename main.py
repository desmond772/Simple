import asyncio
import os
import logging
import socketio
import json
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load environment variables
load_dotenv()

# Get the Pocket Option SSID from the environment variable.
SSID_MESSAGE = os.environ.get('POCKET_OPTION_SSID')
if not SSID_MESSAGE:
    logging.critical("POCKET_OPTION_SSID environment variable not set. Exiting.")
    exit(1)

# The Socket.IO URL
SOCKETIO_URL = "wss://api-in.pocketoption.com:8095"

# Create an async Socket.IO client instance
sio = socketio.AsyncClient()

@sio.event
async def connect():
    """Event handler for successful connection."""
    logging.info("Connected to Pocket Option WebSocket server via Socket.IO.")
    logging.info("Sending authentication message...")
    
    try:
        # Parse the JSON string from your SSID_MESSAGE.
        # It assumes the format is always '42' followed by the JSON string.
        message_payload = json.loads(SSID_MESSAGE[2:])
        
        # The first element is the event name, the second is the data.
        # Pocket Option likely expects the event name "auth" and the session data.
        event_name = message_payload[0]
        event_data = message_payload[1]
        
        # Send the authentication event and data.
        await sio.emit(event_name, event_data)
        logging.info("Authentication message sent.")
    except (json.JSONDecodeError, IndexError, Exception) as e:
        logging.error(f"Error parsing or sending authentication message: {e}")

@sio.event
async def disconnect():
    """Event handler for disconnection."""
    logging.info("Disconnected from Pocket Option WebSocket server.")

@sio.event
async def message(data):
    """Event handler for received messages."""
    logging.info(f"Received message: {data}")
    # Add your custom logic here

async def main():
    """Main function to connect and run the client."""
    try:
        # Use the `headers` parameter to add an Origin header.
        await sio.connect(SOCKETIO_URL, headers={'Origin': 'https://pocketoption.com'})
        await sio.wait()
    except socketio.exceptions.ConnectionError as e:
        logging.critical(f"Connection failed: {e}")
    except Exception as e:
        logging.critical(f"An unexpected fatal error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
