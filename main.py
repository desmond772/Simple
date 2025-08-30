import os
import asyncio
import socketio
import logging
from dotenv import load_dotenv

# Set up logging to provide detailed debug information
logging.basicConfig(level=logging.DEBUG)

# Load environment variables
load_dotenv()

# Get environment variables
POCKET_OPTION_SSID = os.getenv("POCKET_OPTION_SSID")
WEBSOCKET_URL = os.getenv("WEBSOCKET_URL")
ORIGIN = os.getenv("ORIGIN")

# Create an async Socket.IO client instance with detailed logging
sio = socketio.AsyncClient(logger=True, engineio_logger=True)

# Event handler for successful connection
@sio.event
async def connect():
    print("Socket.IO connection established.")
    print("Authenticating with Pocket Option...")
    # The 'auth' event should be sent immediately after connecting
    # The payload format is crucial, so we stick to the official Socket.IO spec
    await sio.emit('auth', {"session": POCKET_OPTION_SSID, "isDemo": 0})

# Event handler for a failed connection attempt
@sio.event
async def connect_error(data):
    print("The connection failed!")

# Event handler for disconnection
@sio.event
async def disconnect():
    print("Socket.IO disconnected.")

# Event handler for the 'profile' message, which should contain the balance
@sio.on('profile')
async def on_profile(data):
    print("Received profile info:")
    balance = data.get("balance")
    demo_balance = data.get("demoBalance")
    currency = data.get("currency")
    print(f"Balance: {balance}")
    print(f"Demo Balance: {demo_balance}")
    print(f"Currency: {currency}")

# Catch-all event handler to log any unknown messages from the server
@sio.on('*')
async def catch_all(event, data):
    if event not in ['connect', 'disconnect', 'auth', 'profile']:
        print(f"Received unknown event '{event}' with data: {data}")

async def main():
    if not WEBSOCKET_URL or not POCKET_OPTION_SSID:
        print("Error: Missing environment variables. Check your .env file.")
        return

    try:
        # The socket.io client handles the Engine.IO handshake and upgrade process automatically
        # It's best to strip the query parameters and let the library handle them
        stripped_url = WEBSOCKET_URL.split('/socket.io')[0]
        await sio.connect(url=stripped_url, transports=['websocket'])

        # Wait forever to keep the connection alive and process events
        await sio.wait()

    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        await sio.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nScript interrupted by user. Exiting...")
