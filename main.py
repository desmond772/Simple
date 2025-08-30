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
    """Listens for and processes incoming messages from the WebSocket."""
    while True:
        try:
            message = await websocket.recv()
            
            # Pocket Option's Socket.IO protocol adds a '42' prefix to events.
            if message.startswith('42'):
                try:
                    # Strip the prefix and parse the JSON data.
                    event_data = json.loads(message[2:])
                    event_name = event_data[0] # The event name is the first element
                    payload = event_data[1]    # The payload is the second element

                    # Route based on the event name.
                    if event_name == 'auth_success':
                        # The 'auth' event from the server indicates a success or failure response.
                        print(f"Authentication successful: {payload}")
                        print("Requesting user balance...")
                        
                        # Send the 'profile/balance/get' request.
                        balance_request = ['profile/balance/get', {}]
                        await websocket.send(f'42{json.dumps(balance_request)}')
                    
                    elif event_name == 'profile/balance/get':
                        print(f"User balance received: {payload}")
                    
                    elif event_name == 'message':
                        print(f"Received message: {payload}")

                    else:
                        print(f"Received event '{event_name}': {payload}")

                except json.JSONDecodeError:
                    print(f"Received non-JSON message starting with '42': {message}")
            
            else:
                # Handle other message types, such as pings/pongs from the engine.
                if message == '3':
                    # Respond to a ping with a pong to keep the connection alive.
                    await websocket.send('2')
                else:
                    print(f"Received message: {message}")
        
        except websockets.exceptions.ConnectionClosed as e:
            print(f"Connection closed: {e}")
            break
        except Exception as e:
            print(f"An error occurred while receiving a message: {e}")
            break # Exit the loop on other errors

async def main():
    """Manages the WebSocket connection lifecycle."""
    if not WEBSOCKET_URL or not POCKET_OPTION_SSID:
        print("Error: WEBSOCKET_URL or POCKET_OPTION_SSID not found. Check your .env file.")
        return

    # Pocket Option's WebSocket URL likely requires a `wss` prefix
    # and includes the Engine.IO path and query parameters for the session.
    websocket_url = f"{WEBSOCKET_URL}/socket.io/?EIO=4&transport=websocket"

    # Headers to mimic a web browser connection.
    # Note: Use 'additional_headers' for recent versions of 'websockets'.
    headers = {
        "Origin": ORIGIN,
        "Cookie": f"ssid={POCKET_OPTION_SSID}",
    }

    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"

    print(f"Attempting to connect to raw WebSocket at {websocket_url}...")
    try:
        # Pass headers using 'additional_headers' and 'user_agent_header'.
        async with websockets.connect(
            websocket_url,
            additional_headers=headers,
            user_agent_header=user_agent
        ) as websocket:
            print("WebSocket connection established.")

            # The server will respond with the initial '0' and handshake data.
            # Then we can proceed with authentication.
            initial_message = await websocket.recv()
            print(f"Received initial handshake: {initial_message}")
            
            # Send the 'auth' message in the Socket.IO format ('42').
            auth_payload = {
                "session": POCKET_OPTION_SSID,
                "isDemo": 1,
                "platform": 3,
            }
            auth_message = ['auth', auth_payload]
            await websocket.send(f'42{json.dumps(auth_message)}')
            print("Authentication message sent.")

            # Start listening for incoming messages in a loop.
            await receive_messages(websocket)

    except websockets.exceptions.InvalidURI:
        print(f"Error: Invalid WebSocket URI. Check if '{WEBSOCKET_URL}' is correct.")
    except Exception as e:
        print(f"Failed to connect to the WebSocket server: {e}")

if __name__ == "__main__":
    asyncio.run(main())
                        
