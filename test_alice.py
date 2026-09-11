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
        # 2. Login as Alice
        # --------------------------------------------------
        await websocket.send(
            json.dumps({
                "type": "login",
                "username": "Alice"
            })
        )

        login_response = await receive_json(
            websocket,
            "Login response"
        )

        if not login_response.get("success"):
            print("\nAlice login failed.")
            return

        alice = login_response["user"]
        alice_id = alice["user_id"]

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
        # 5. Create conversation with Bob
        # --------------------------------------------------
        await websocket.send(
            json.dumps({
                "type": "create_conversation",
                "name": "Alice and Bob",
                "participant_ids": [1, 2]
            })
        )

        create_response = await receive_json(
            websocket,
            "Create conversation response"
        )

        if not create_response.get("success"):
            print("\nConversation creation failed.")
            return

        conversation = create_response["conversation"]
        conversation_id = conversation["conversation_id"]

        print(
            f"\nUsing conversation ID: {conversation_id}"
        )

        # --------------------------------------------------
        # 6. Send message
        # --------------------------------------------------
        await websocket.send(
            json.dumps({
                "type": "send_message",
                "conversation_id": conversation_id,
                "content": "Hello Bob!"
            })
        )

        # The server broadcasts the new message to
        # all connected participants, including Alice.
        await receive_json(
            websocket,
            "New message received"
        )

        # --------------------------------------------------
        # 7. Get message history
        # --------------------------------------------------
        await websocket.send(
            json.dumps({
                "type": "get_messages",
                "conversation_id": conversation_id
            })
        )

        await receive_json(
            websocket,
            "Message history"
        )

        # --------------------------------------------------
        # 8. Keep Alice connected
        # --------------------------------------------------
        print("\nAlice is connected.")
        print("Waiting for messages...")

        try:
            while True:
                response = await websocket.recv()

                print("\nReceived:")
                print(
                    json.dumps(
                        json.loads(response),
                        indent=2
                    )
                )

        except websockets.exceptions.ConnectionClosed:
            print("\nAlice connection closed.")


if __name__ == "__main__":
    asyncio.run(test())