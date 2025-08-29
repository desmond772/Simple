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
sio = socketio.AsyncClient()

@sio.event
async def connect():
    """Event handler for successful connection."""
    print("Socket.IO connection established.")
    
    # Send the authentication payload as a Python dictionary.
    # The library will format it correctly to 42["auth",{...}]
    auth_payload = {
        "session": POCKET_OPTION_SSID,
        "isDemo": 1,  # Set to 1 for demo account, 0 for real account
        "platform": 3, # A common platform identifier
    }
    await sio.emit('auth', auth_payload)
    print("Authentication message sent.")

@sio.event
async def disconnect():
    """Event handler for disconnection."""
    print("Disconnected from the Socket.IO server.")

@sio.event
async def message(data):
    """Event handler for incoming messages."""
    print(f"Received message: {data}")

@sio.event
async def connect_error(data):
    """Event handler for connection errors."""
    print(f"Connection to server failed: {data}")

async def main():
    """Main function to start and run the connection."""
    headers = {
        "Origin": ORIGIN,
        "Cookie": f"ssid={POCKET_OPTION_SSID}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
    }

    try:
        # Try connecting with Socket.IO transports and engineio version 3
        # These versions are often more compatible with brokerage APIs.
        await sio.connect(WEBSOCKET_URL, headers=headers, transports=['websocket'], engineio_versions=['3'])
        
        await sio.wait()

    except socketio.exceptions.ConnectionError as e:
        print(f"Failed to connect to Socket.IO server: {e}")

if __name__ == "__main__":
    if not WEBSOCKET_URL or not POCKET_OPTION_SSID:
        print("Error: WEBSOCKET_URL or POCKET_OPTION_SSID not found. Check your .env file.")
    else:
        asyncio.run(main())
    
