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
            if message == "2":
                print("Received ping, sending pong")
                await websocket.send("3")  # Send pong response
            elif message.startswith('42["profile",'):
                profile_info = json.loads(message[3:])[1]
                balance = profile_info.get("balance")
                demo_balance = profile_info.get("demoBalance")
                currency = profile_info.get("currency")
                print(f"Balance: {balance}")
                print(f"Demo Balance: {demo_balance}")
                print(f"Currency: {currency}")
            else:
                print(f"Received message: {message}")
    except websockets.exceptions.ConnectionClosed as e:
        print(f"Connection closed: {e.code} {e.reason}")
        await reconnect(websocket)
    except Exception as e:
        print(f"Error receiving messages: {e}")

async def send_authentication(websocket):
    try:
        auth_payload = f'42["auth",{{"session":"{POCKET_OPTION_SSID}","isDemo":0}}]'
        await websocket.send(auth_payload)
        print("Authentication message sent.")
    except Exception as e:
        print(f"Error sending authentication: {e}")

async def get_balance(websocket):
    try:
        balance_payload = '42["profile"]'
        await websocket.send(balance_payload)
        print("Balance request sent.")
    except Exception as e:
        print(f"Error sending balance request: {e}")

async def reconnect(websocket):
    try:
        await websocket.close()
        await asyncio.sleep(5)
        async with websockets.connect(
            WEBSOCKET_URL,
            additional_headers={"Origin": ORIGIN},
            open_timeout=10,
        ) as new_websocket:
            print("Reconnected to WebSocket")
            await send_authentication(new_websocket)
            await get_balance(new_websocket)
            await receive_messages(new_websocket)
    except Exception as e:
        print(f"Error reconnecting: {e}")

# Main function
async def main():
    if not WEBSOCKET_URL or not POCKET_OPTION_SSID:
        print("Error: Missing environment variables. Check your .env file.")
        return

    headers = {
        "Origin": ORIGIN,
    }

    try:
        async with websockets.connect(
            WEBSOCKET_URL,
            additional_headers=headers,
            open_timeout=10,
        ) as websocket:
            print("WebSocket connection established.")
            await send_authentication(websocket)
            await get_balance(websocket)
            await receive_messages(websocket)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
