import asyncio
import json
import websockets


async def test():
    uri = "ws://localhost:8765"

    async with websockets.connect(uri) as websocket:

        response = await websocket.recv()
        print("Connected response:")
        print(json.dumps(json.loads(response), indent=2))

        await websocket.send(json.dumps({
            "type": "login",
            "username": "Alice"
        }))

        response = await websocket.recv()
        print("\nLogin response:")
        print(json.dumps(json.loads(response), indent=2))

        response = await websocket.recv()
        print("\nUser list:")
        print(json.dumps(json.loads(response), indent=2))

        response = await websocket.recv()
        print("\nUser status:")
        print(json.dumps(json.loads(response), indent=2))

        await websocket.send(json.dumps({
            "type": "get_users"
        }))

        response = await websocket.recv()
        print("\nGet users response:")
        print(json.dumps(json.loads(response), indent=2))

        await websocket.send(json.dumps({
            "type": "create_conversation",
            "name": "Alice and Bob",
            "participant_ids": [1, 2]
        }))

        response = await websocket.recv()
        create_response = json.loads(response)

        print("\nCreate conversation response:")
        print(json.dumps(create_response, indent=2))

        conversation_id = create_response["conversation"]["conversation_id"]

        print(f"\nUsing conversation ID: {conversation_id}")

        await websocket.send(json.dumps({
            "type": "send_message",
            "conversation_id": conversation_id,
            "content": "Hello Bob!"
        }))

        response = await websocket.recv()

        print("\nSend message response:")
        print(json.dumps(json.loads(response), indent=2))

        # GET MESSAGE HISTORY
        await websocket.send(json.dumps({
            "type": "get_messages",
            "conversation_id": conversation_id
        }))

        response = await websocket.recv()

        print("\nMessage history:")
        print(json.dumps(json.loads(response), indent=2))

        print("\nAlice is connected.")
        print("Waiting for messages...")

        try:
            async for message in websocket:
                print("\nReceived:")
                print(json.dumps(json.loads(message), indent=2))

        except websockets.exceptions.ConnectionClosed:
            print("Disconnected from server.")


asyncio.run(test())