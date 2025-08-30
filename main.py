import os
import asyncio
import socketio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get environment variables
POCKET_OPTION_SSID = os.getenv("POCKET_OPTION_SSID")
WEBSOCKET_URL = os.getenv("WEBSOCKET_URL")
ORIGIN = os.getenv("ORIGIN")

# Create an async Socket.IO client instance
sio = socketio.AsyncClient()

@sio.event
async def connect():
    print("Socket.IO connection established.")
    print("Authenticating with Pocket Option...")
    await sio.emit('auth', {"session": POCKET_OPTION_SSID, "isDemo": 0})

@sio.event
async def disconnect():
    print("Socket.IO disconnected.")

@sio.event
async def profile(data):
    print("Received profile info:")
    balance = data.get("balance")
    demo_balance = data.get("demoBalance")
    currency = data.get("currency")
    print(f"Balance: {balance}")
    print(f"Demo Balance: {demo_balance}")
    print(f"Currency: {currency}")

@sio.on('*')
async def catch_all(event, data):
    """
    Catch-all for any other events from the server, useful for debugging.
    """
    print(f"Received event '{event}' with data: {data}")

async def main():
    if not WEBSOCKET_URL or not POCKET_OPTION_SSID:
        print("Error: Missing environment variables. Check your .env file.")
        return

    try:
        # Note: socket.io client uses a different connection URL format
        # It handles the EIO and transport parameters automatically
        stripped_url = WEBSOCKET_URL.split('/socket.io')[0]
        await sio.connect(url=stripped_url, transports=['websocket'])

        # Wait forever to keep the connection alive and process events
        await sio.wait()

    except socketio.exceptions.ConnectionError as e:
        print(f"Connection failed: {e}")
    except KeyboardInterrupt:
        print("\nScript interrupted by user. Exiting...")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        await sio.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
    
