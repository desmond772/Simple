import asyncio
import os
import logging
import socketio
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

# The Socket.IO URL is different and does not contain the EIO or transport parameters.
# The `python-socketio` library handles this automatically.
# Use the correct base URL for Pocket Option's Socket.IO server.
SOCKETIO_URL = "wss://api-in.pocketoption.com:8095"

# Create an async Socket.IO client instance
sio = socketio.AsyncClient()

@sio.event
async def connect():
    """Event handler for successful connection."""
    logging.info("Connected to Pocket Option WebSocket server via Socket.IO.")
    logging.info("Sending authentication message...")
    # The Socket.IO library handles the EIO and transport details,
    # so you only need to send the final message.
    # Note: Your original SSID format might be incorrect for the Socket.IO client.
    # The payload likely needs to be a standard JSON string or object.
    # You may need to adapt this part based on Pocket Option's API documentation.
    # This example assumes the payload is a valid JSON string.
    try:
        await sio.send(SSID_MESSAGE)
        logging.info("Authentication message sent.")
    except Exception as e:
        logging.error(f"Failed to send authentication message: {e}")

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
        await sio.connect(SOCKETIO_URL)
        await sio.wait()
    except socketio.exceptions.ConnectionError as e:
        logging.critical(f"Connection failed: {e}")
    except Exception as e:
        logging.critical(f"An unexpected fatal error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
    
