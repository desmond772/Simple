import os
import socketio
import asyncio
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Get environment variables
POCKET_OPTION_SSID = os.getenv("POCKET_OPTION_SSID")
WEBSOCKET_URL = os.getenv("WEBSOCKET_URL")
ORIGIN = os.getenv("ORIGIN")

# Create a Socket.IO client instance
sio = socketio.AsyncClient(
    reconnection=True,
    reconnection_attempts=0,
    reconnection_delay=1,
    reconnection_delay_max=5,
    randomization_factor=0.5,
    logger=True,
    engineio_logger=True,
    engineio_options={
        'ping_interval': 20,
        'transports': ['websocket']
    }
)

@sio.event
async def connect():
    """Fired when the connection is successfully established or re-established."""
    print("Socket.IO connection established.")

    auth_payload = {
        "session": POCKET_OPTION_SSID,
        "isDemo": 1,
        "platform": 3,
    }
    await sio.emit('auth', auth_payload)
    print("Authentication message sent. Waiting for response...")

@sio.event
async def auth_success(data):
    """Fired upon successful authentication, as confirmed by Pocket Option."""
    print(f"Authentication successful: {data}")

    print("Requesting user balance...")
    await sio.emit('profile/balance/get', {})

@sio.event
async def profile_balance_get(data):
    """Handles the user balance data received from the server."""
    print(f"User balance received: {data}")

@sio.event
async def disconnect():
    """Fired on both intentional and accidental disconnections."""
    print("Disconnected from the Socket.IO server.")

@sio.event
async def message(data):
    """Receives general messages from the server."""
    print(f"Received message: {data}")

@sio.event
async def connect_error(data):
    """Fired when a connection attempt fails."""
    print(f"Connection to server failed: {data}")

async def main():
    """The main function to manage the client lifecycle."""
    if not WEBSOCKET_URL or not POCKET_OPTION_SSID:
        print("Error: WEBSOCKET_URL or POCKET_OPTION_SSID not found. Check your .env file.")
        return

    headers = {
        "Origin": ORIGIN,
        "Cookie": f"ssid={POCKET_OPTION_SSID}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
    }

    print(f"Attempting to connect to {WEBSOCKET_URL}...")
    try:
        await sio.connect(WEBSOCKET_URL, headers=headers)
        await sio.wait()
    except socketio.exceptions.ConnectionError as e:
        print(f"Failed to establish initial connection to Socket.IO server: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())

