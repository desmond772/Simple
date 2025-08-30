import os
import asyncio
import json
import websockets
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Get environment variables
POCKET_OPTION_SSID = os.getenv("POCKET_OPTION_SSID")
WEBSOCKET_URL = os.getenv("WEBSOCKET_URL")
ORIGIN = os.getenv("ORIGIN")

async def receive_messages(websocket):
    """Continuously listen for and print messages from the server."""
    try:
        async for message in websocket:
            print(f"Received message: {message}")
    except websockets.exceptions.ConnectionClosed:
        print("Connection closed.")

async def send_authentication(websocket):
    """Send the authentication message to the server."""
    auth_payload = {"session": POCKET_OPTION_SSID}
    await websocket.send(json.dumps(auth_payload))
    print("Authentication message sent.")

async def main():
    """Main function to start and manage the connection."""
    if not WEBSOCKET_URL or not POCKET_OPTION_SSID:
        print("Error: WEBSOCKET_URL or POCKET_OPTION_SSID not found. Check your .env file.")
        return

    # Use a more complete set of headers to mimic a browser
    headers = {
        "Origin": ORIGIN,
        "Cookie": f"ssid={POCKET_OPTION_SSID}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/533.36",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Connection": "Upgrade",
        "Upgrade": "websocket",
        "Sec-WebSocket-Version": "13",
        # Important: You must inspect browser traffic for additional required headers,
        # such as Sec-WebSocket-Key and adjust as needed.
        # It is unique per connection so not hardcoded here.
    }
    
    # Define a timeout to prevent the connection attempt from hanging indefinitely
    connection_timeout = 10 

    try:
        # Establish the WebSocket connection, using additional_headers
        async with websockets.connect(
            WEBSOCKET_URL,
            additional_headers=headers,
            open_timeout=connection_timeout
        ) as websocket:
            print("WebSocket connection established.")
            
            # Create tasks for sending authentication and receiving messages
            auth_task = asyncio.create_task(send_authentication(websocket))
            receive_task = asyncio.create_task(receive_messages(websocket))
            
            # Wait for all tasks to complete (or for the script to be manually stopped)
            await asyncio.gather(auth_task, receive_task)

    except websockets.exceptions.InvalidStatusCode as e:
        print(f"Connection failed with status code: {e.status_code}. The server rejected the connection.")
        print(f"Possible causes: Invalid/expired SSID, or missing/incorrect headers.")
    except (websockets.exceptions.WebSocketException, asyncio.TimeoutError) as e:
        print(f"Failed to connect to WebSocket server: {e}")

if __name__ == "__main__":
    asyncio.run(main())
    
