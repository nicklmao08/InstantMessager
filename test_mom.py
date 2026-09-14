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
        # 2. Login as Mom
        # --------------------------------------------------
        await websocket.send(
            json.dumps({
                "type": "login",
                "username": "Mom"
            })
        )

        login_response = await receive_json(
            websocket,
            "Login response"
        )

        if not login_response.get("success"):
            print("\nMom login failed.")
            return

        mom = login_response["user"]
        mom_id = mom["user_id"]

        print(f"\nMom user ID: {mom_id}")

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

        users_response = await receive_json(
            websocket,
            "Get users response"
        )

        users = users_response.get("users", [])

        user_ids = {}

        for user in users:
            user_ids[user["username"]] = user["user_id"]

        print("\nUsers found:")
        print(json.dumps(user_ids, indent=2))

        # --------------------------------------------------
        # 5. Check that Dad and Brother are connected
        # --------------------------------------------------
        if "Dad" not in user_ids:
            print("\nDad is not connected.")
            return

        if "Brother" not in user_ids:
            print("\nBrother is not connected.")
            return

        # --------------------------------------------------
        # 6. Create family group
        # --------------------------------------------------
        participant_ids = [
            user_ids["Mom"],
            user_ids["Dad"],
            user_ids["Brother"]
        ]

        await websocket.send(
            json.dumps({
                "type": "create_conversation",
                "name": "Family Group",
                "participant_ids": participant_ids
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
        # 7. Send group message
        # --------------------------------------------------
        await websocket.send(
            json.dumps({
                "type": "send_message",
                "conversation_id": conversation_id,
                "content": "Hello Dad and Brother!"
            })
        )

        # The server broadcasts the message to
        # all participants: Mom, Dad, and Brother.
        await receive_json(
            websocket,
            "New message received"
        )

        # --------------------------------------------------
        # 8. Get message history
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
        # 9. Keep Mom connected
        # --------------------------------------------------
        print("\nMom is connected.")
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
            print("\nMom connection closed.")


if __name__ == "__main__":
    asyncio.run(test())