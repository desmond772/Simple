import os
import asyncio
import socketio
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get environment variables
POCKET_OPTION_SSID = os.getenv("POCKET_OPTION_SSID")
USER_ID = os.getenv("USER_ID")
WEBSOCKET_URL = os.getenv("WEBSOCKET_URL")
ORIGIN = os.getenv("ORIGIN")

if not all([POCKET_OPTION_SSID, USER_ID, WEBSOCKET_URL, ORIGIN]):
    print("Error: Missing environment variables. Check your .env file.")
    exit(1)

# Create an async Socket.IO client instance with detailed logging
sio = socketio.AsyncClient(logger=True, engineio_logger=True)

# Event handler for successful connection
@sio.event
async def connect():
    print("Socket.IO connection established.")
    # Note: Authentication is now handled within the sio.connect() call.
    # The server should respond to the authentication and then send events.

# Event handler for connection errors
@sio.event
async def connect_error(data):
    print(f"The connection failed! Data: {data}")

# Event handler for disconnection, now with reason
@sio.event
async def disconnect(reason):
    print(f"Socket.IO disconnected. Reason: {reason}")
    if "Unauthorized" in reason:
        print("Authentication likely failed. Check your SSID and other credentials.")
    elif "transport close" in reason:
        print("Transport closed, possibly due to a connection error or authentication failure.")

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
    if event not in ['connect', 'disconnect', 'profile', 'auth', 'connect_error']:
        print(f"Received unknown event '{event}' with data: {data}")

async def main():
    headers = {'Origin': ORIGIN}
    auth_payload = {
        "session": POCKET_OPTION_SSID,
        "isDemo": 1,  # Set to 0 for a real account
        "uid": int(USER_ID),
        "platform": 1
    }
    
    try:
        await sio.connect(
            url=WEBSOCKET_URL,
            transports=['websocket'],
            headers=headers,
            auth=auth_payload
        )
        await sio.wait()
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        if sio.connected:
            await sio.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nScript interrupted by user. Exiting...")
    
