import os
import asyncio
import json
import websockets
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get environment variables
POCKET_OPTION_SSID = os.getenv("POCKET_OPTION_SSID")
WEBSOCKET_URL = os.getenv("WEBSOCKET_URL")
ORIGIN = os.getenv("ORIGIN")

# Define functions for handling messages and authentication
async def receive_messages(websocket):
    try:
        async for message in websocket:
            print(f"Received message: {message}")
    except websockets.exceptions.ConnectionClosed as e:
        print(f"Connection closed: {e}")
    except Exception as e:
        print(f"Error receiving messages: {e}")

async def send_authentication(websocket):
    try:
        auth_payload = f'42["auth",{{"session":"{POCKET_OPTION_SSID}","isDemo":0}}]'
        await websocket.send(auth_payload)
        print("Authentication message sent.")
    except Exception as e:
        print(f"Error sending authentication: {e}")

# Main function
async def main():
    if not WEBSOCKET_URL or not POCKET_OPTION_SSID:
        print("Error: Missing environment variables. Check your .env file.")
        return

    headers = {
        "Origin": ORIGIN,
    }

    connection_timeout = 10
    try:
        async with websockets.connect(
            WEBSOCKET_URL,
            additional_headers=headers,
            open_timeout=connection_timeout,
        ) as websocket:
            print("WebSocket connection established.")
            auth_task = asyncio.create_task(send_authentication(websocket))
            receive_task = asyncio.create_task(receive_messages(websocket))
            await asyncio.gather(auth_task, receive_task)
    except websockets.exceptions.InvalidStatus as e:
        print(f"Connection failed with status code: {e.response.status_code}.")
        print(f"Possible causes: Invalid/expired SSID, or missing/incorrect headers.")
    except websockets.exceptions.ConnectionClosed as e:
        print(f"Connection closed: {e}")
    except asyncio.TimeoutError:
        print("Connection timed out.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
