import asyncio
import json
import websockets


async def test():
    uri = "ws://localhost:8765"

    try:
        async with websockets.connect(uri) as websocket:

            print("Connected to server!")

            await websocket.send(json.dumps({
                "type": "login",
                "username": "Bob"
            }))
 
            async for message in websocket:
                data = json.loads(message)

                print("Received:")
                print(json.dumps(data, indent=2))

    except websockets.exceptions.ConnectionClosed:
        print("Disconnected from server.")


asyncio.run(test())