import asyncio
import json

import websockets


SERVER_URI = "ws://localhost:8765"


async def receive_json(websocket, label):
    """Receive and print one JSON message."""
    response = json.loads(await websocket.recv())

    print(f"\n{label}:")
    print(json.dumps(response, indent=2))

    return response


async def test():
    async with websockets.connect(SERVER_URI) as websocket:

        # --------------------------------------------------
        # 1. Connection
        # --------------------------------------------------
        await receive_json(
            websocket,
            "Connected response"
        )

        # --------------------------------------------------
        # 2. Login as Dad
        # --------------------------------------------------
        await websocket.send(
            json.dumps({
                "type": "login",
                "username": "Dad"
            })
        )

        login_response = await receive_json(
            websocket,
            "Login response"
        )

        if not login_response.get("success"):
            print("\nDad login failed.")
            return

        dad = login_response["user"]
        dad_id = dad["user_id"]

        print(f"\nDad user ID: {dad_id}")

        # --------------------------------------------------
        # 3. Initial user list and status
        # --------------------------------------------------
        await receive_json(
            websocket,
            "User list"
        )

        await receive_json(
            websocket,
            "User status"
        )

        # --------------------------------------------------
        # 4. Get users
        # --------------------------------------------------
        await websocket.send(
            json.dumps({
                "type": "get_users"
            })
        )

        await receive_json(
            websocket,
            "Get users response"
        )

        # --------------------------------------------------
        # 5. Get conversations
        # --------------------------------------------------
        await websocket.send(
            json.dumps({
                "type": "get_conversations"
            })
        )

        conversation_response = await receive_json(
            websocket,
            "Conversation list"
        )

        conversations = conversation_response.get(
            "conversations",
            []
        )

        if conversations:
            print("\nDad can see these conversations:")
            print(json.dumps(conversations, indent=2))
        else:
            print("\nNo conversations found for Dad.")

        # --------------------------------------------------
        # 6. Keep Dad connected
        # --------------------------------------------------
        print("\nDad is connected.")
        print("Waiting for group messages...")

        try:
            while True:
                response = await websocket.recv()

                message = json.loads(response)

                print("\nReceived:")
                print(json.dumps(message, indent=2))

        except websockets.exceptions.ConnectionClosed:
            print("\nDad connection closed.")


if __name__ == "__main__":
    asyncio.run(test())