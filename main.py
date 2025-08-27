import asyncio
import json
import websockets
import os
import logging
from dotenv import load_dotenv

# Load environment variables from the .env file.
# This must be done at the beginning of the script.
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Get the SSID from the environment variable.
SSID_MESSAGE = os.environ.get('POCKET_OPTION_SSID')

if not SSID_MESSAGE:
    logging.critical("POCKET_OPTION_SSID environment variable not set. Exiting.")
    exit(1)

# Note: Your URL may not be correct, you should verify it with developer tools.
WEBSOCKET_URL = "wss://ws.pocketoption.com/socket.io/?EIO=3&transport=websocket"

async def connect_to_pocket_option():
    """
    Connects to the Pocket Option WebSocket server and authenticates.
    """
    logging.info("Attempting to connect to Pocket Option WebSocket.")
    try:
        async with websockets.connect(WEBSOCKET_URL) as websocket:
            logging.info("Connected to Pocket Option WebSocket.")

            await receive_and_print_messages(websocket, 2)

            logging.info("Sending authentication message...")
            await websocket.send(SSID_MESSAGE)
            logging.info("Authentication message sent.")

            while True:
                response = await websocket.recv()
                logging.info(f"Received message: {response}")

    except websockets.exceptions.ConnectionClosed as e:
        logging.error(f"Connection closed unexpectedly: {e}")
    except Exception as e:
        logging.critical(f"An unexpected fatal error occurred: {e}")

async def receive_and_print_messages(websocket, count):
    """
    Helper function to receive and print a specific number of messages.
    """
    for _ in range(count):
        message = await websocket.recv()
        logging.info(f"Initial server message: {message}")

if __name__ == "__main__":
    asyncio.run(connect_to_pocket_option())
  
