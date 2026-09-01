import asyncio
import json
import websockets


async def test():

    uri = "ws://localhost:8765"

    async with websockets.connect(uri) as websocket:

        print("Connected to server!")

        # =========================
        # LOGIN
        # =========================

        await websocket.send(json.dumps({
            "type": "login",
            "username": "Alice"
        }))

        response = await websocket.recv()

        print("Login response:")
        print(response)

        # =========================
        # USER LIST
        # =========================

        user_list = await websocket.recv()

        print("Online users:")
        print(user_list)

        # =========================
        # SEND MESSAGE
        # =========================

        await websocket.send(json.dumps({
            "type": "send_message",
            "to": "Bob",
            "content": "Hello Bob!"
        }))

        print("Message sent!")

        # =========================
        # KEEP CONNECTION OPEN
        # =========================

        print("Connected. Press Ctrl+C to disconnect.")

        try:
            async for message in websocket:

                print("Received:")
                print(
                    json.dumps(
                        json.loads(message),
                        indent=2
                    )
                )

        except websockets.exceptions.ConnectionClosed:
            print("Disconnected.")


asyncio.run(test())