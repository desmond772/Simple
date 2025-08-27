import asyncio
import json
import websockets
import os
import logging
from dotenv import load_dotenv

# Configure logging to display INFO messages and above.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load environment variables from the .env file for local testing.
load_dotenv()

# Get the SSID from the environment variable.
SSID_MESSAGE = os.environ.get('POCKET_OPTION_SSID')

if not SSID_MESSAGE:
    logging.critical("POCKET_OPTION_SSID environment variable not set. Exiting.")
    exit(1)

# CORRECTED: Use the known, working WebSocket URL.
# The previous URL was causing the "Name or service not known" error.
WEBSOCKET_URL = "wss://api-in.pocketoption.com:8095/socket.io/?EIO=3&transport=websocket"

async def connect_to_pocket_option():
    """
    Connects to the Pocket Option WebSocket server and authenticates.
    """
    logging.info("Attempting to connect to Pocket Option WebSocket.")
    try:
        async with websockets.connect(WEBSOCKET_URL) as websocket:
            logging.info("Connected to Pocket Option WebSocket.")

            # Wait for initial server messages to establish the Socket.IO session.
            await receive_and_print_messages(websocket, 2)

            # Authenticate with the server using your SSID message.
            logging.info("Sending authentication message...")
            await websocket.send(SSID_MESSAGE)
            logging.info("Authentication message sent.")

            # Listen for subsequent server messages.
            while True:
                response = await websocket.recv()
                logging.info(f"Received message: {response}")
                # Add your custom logic here for trading, balance updates, etc.

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
    
