import asyncio
import json
import websockets


SERVER_URL = "ws://localhost:8765"
USERNAME = "Dad"

OTHER_USERS = [
    "Mom",
    "Brother"
]


async def receive_until(
    websocket,
    expected_type
):
    while True:

        response = await websocket.recv()

        data = json.loads(
            response
        )

        print("\nReceived:")
        print(
            json.dumps(
                data,
                indent=2
            )
        )

        if data.get("type") == expected_type:
            return data


async def wait_for_users(
    websocket,
    required_names
):
    while True:

        await websocket.send(
            json.dumps({
                "type": "get_users"
            })
        )

        data = await receive_until(
            websocket,
            "user_list"
        )

        users = data.get(
            "users",
            []
        )

        usernames = {
            user.get("username")
            for user in users
        }

        if all(
            name in usernames
            for name in required_names
        ):

            return users

        print(
            "\nWaiting for other users..."
        )

        await asyncio.sleep(1)


def build_user_map(users):

    result = {}

    for user in users:

        username = user.get(
            "username"
        )

        user_id = user.get(
            "user_id"
        )

        if username and user_id is not None:

            result[username] = user_id

    return result


def find_conversation(
    conversations,
    participant_ids
):

    wanted = set(
        participant_ids
    )

    for conversation in conversations:

        existing = set(
            conversation.get(
                "participants",
                []
            )
        )

        if existing == wanted:
            return conversation

    return None


async def get_conversations(
    websocket
):

    await websocket.send(
        json.dumps({
            "type": "get_conversations"
        })
    )

    data = await receive_until(
        websocket,
        "conversation_list"
    )

    return data.get(
        "conversations",
        []
    )


async def get_or_create_conversation(
    websocket,
    conversations,
    name,
    participant_ids
):

    conversation = find_conversation(
        conversations,
        participant_ids
    )

    if conversation is not None:

        print(
            f"\nUsing existing conversation "
            f"{conversation['conversation_id']}: "
            f"{conversation['name']}"
        )

        return conversation

    await websocket.send(
        json.dumps({
            "type": "create_conversation",
            "name": name,
            "participant_ids": participant_ids
        })
    )

    response = await receive_until(
        websocket,
        "create_conversation_response"
    )

    if not response.get("success"):

        raise RuntimeError(
            "Failed to create conversation."
        )

    return response[
        "conversation"
    ]


async def get_history(
    websocket,
    conversation_id
):

    await websocket.send(
        json.dumps({
            "type": "get_messages",
            "conversation_id": conversation_id
        })
    )

    data = await receive_until(
        websocket,
        "message_history"
    )

    return data.get(
        "messages",
        []
    )


async def send_message(
    websocket,
    conversation_id,
    content
):

    await websocket.send(
        json.dumps({
            "type": "send_message",
            "conversation_id": conversation_id,
            "content": content
        })
    )

    return await receive_until(
        websocket,
        "new_message"
    )


async def acknowledge_message(
    websocket,
    message_id
):

    print(
        f"\nDad -> delivered "
        f"message {message_id}"
    )

    await websocket.send(
        json.dumps({
            "type": "message_delivered",
            "message_id": message_id
        })
    )

    await asyncio.sleep(1)

    print(
        f"Dad -> read "
        f"message {message_id}"
    )

    await websocket.send(
        json.dumps({
            "type": "message_read",
            "message_id": message_id
        })
    )


async def handle_history_receipts(
    websocket,
    messages,
    user_id
):

    for message in messages:

        if message.get(
            "sender_id"
        ) == user_id:

            continue

        receipts = message.get(
            "receipts",
            {}
        )

        status = receipts.get(
            str(user_id)
        )

        message_id = message.get(
            "message_id"
        )

        if status == "sent":

            print(
                f"\nDad found offline "
                f"message {message_id}."
            )

            await websocket.send(
                json.dumps({
                    "type": "message_delivered",
                    "message_id": message_id
                })
            )

            await asyncio.sleep(0.5)

            await websocket.send(
                json.dumps({
                    "type": "message_read",
                    "message_id": message_id
                })
            )


async def main():

    async with websockets.connect(
        SERVER_URL
    ) as websocket:

        # ----------------------------------------------------
        # CONNECT
        # ----------------------------------------------------

        await receive_until(
            websocket,
            "connected"
        )

        # ----------------------------------------------------
        # LOGIN
        # ----------------------------------------------------

        await websocket.send(
            json.dumps({
                "type": "login",
                "username": USERNAME
            })
        )

        login = await receive_until(
            websocket,
            "login_response"
        )

        if not login.get("success"):

            print(
                "\nDad login failed."
            )

            return

        user_id = login[
            "user"
        ][
            "user_id"
        ]

        print(
            f"\nDad logged in "
            f"with ID {user_id}."
        )

        # ----------------------------------------------------
        # WAIT FOR MOM + BROTHER
        # ----------------------------------------------------

        users = await wait_for_users(
            websocket,
            OTHER_USERS
        )

        user_map = build_user_map(
            users
        )

        mom_id = user_map["Mom"]
        brother_id = user_map["Brother"]

        print(
            "\nUsers:"
        )

        print(
            json.dumps(
                user_map,
                indent=2
            )
        )

        # ----------------------------------------------------
        # GET CONVERSATIONS
        # ----------------------------------------------------

        conversations = await get_conversations(
            websocket
        )

        # ----------------------------------------------------
        # MOM-DAD 1:1
        # ----------------------------------------------------

        mom_dad = await get_or_create_conversation(
            websocket,
            conversations,
            "Mom & Dad",
            [
                user_id,
                mom_id
            ]
        )

        conversations = await get_conversations(
            websocket
        )

        # ----------------------------------------------------
        # DAD-BROTHER 1:1
        # ----------------------------------------------------

        dad_brother = await get_or_create_conversation(
            websocket,
            conversations,
            "Dad & Brother",
            [
                user_id,
                brother_id
            ]
        )

        conversations = await get_conversations(
            websocket
        )

        # ----------------------------------------------------
        # FAMILY GROUP
        # ----------------------------------------------------

        family_group = await get_or_create_conversation(
            websocket,
            conversations,
            "Family Group",
            [
                user_id,
                mom_id,
                brother_id
            ]
        )

        print(
            "\n===================================="
        )

        print(
            "Dad conversations ready:"
        )

        print(
            f"1:1 Dad-Mom      = "
            f"{mom_dad['conversation_id']}"
        )

        print(
            f"1:1 Dad-Brother  = "
            f"{dad_brother['conversation_id']}"
        )

        print(
            f"Family Group     = "
            f"{family_group['conversation_id']}"
        )

        print(
            "===================================="
        )

        # ----------------------------------------------------
        # HISTORY
        # ----------------------------------------------------

        for conversation in [
            mom_dad,
            dad_brother,
            family_group
        ]:

            history = await get_history(
                websocket,
                conversation["conversation_id"]
            )

            print(
                f"\nHistory for "
                f"{conversation['name']}:"
            )

            print(
                json.dumps(
                    history,
                    indent=2
                )
            )

            await handle_history_receipts(
                websocket,
                history,
                user_id
            )

        # ----------------------------------------------------
        # SEND 1:1 TO MOM
        # ----------------------------------------------------

        print(
            "\nSending Dad -> Mom 1:1..."
        )

        message = await send_message(
            websocket,
            mom_dad["conversation_id"],
            "Hi Mom! This is a 1:1 message from Dad."
        )

        print(
            f"\nDad sent message "
            f"{message['message_id']} "
            f"to Mom."
        )

        # ----------------------------------------------------
        # SEND 1:1 TO BROTHER
        # ----------------------------------------------------

        print(
            "\nSending Dad -> Brother 1:1..."
        )

        message = await send_message(
            websocket,
            dad_brother["conversation_id"],
            "Hi Brother! This is a 1:1 message from Dad."
        )

        print(
            f"\nDad sent message "
            f"{message['message_id']} "
            f"to Brother."
        )

        # ----------------------------------------------------
        # SEND GROUP MESSAGE
        # ----------------------------------------------------

        print(
            "\nSending Dad -> Family Group..."
        )

        message = await send_message(
            websocket,
            family_group["conversation_id"],
            "Hello Mom and Brother! - Dad"
        )

        print(
            f"\nDad sent group message "
            f"{message['message_id']}."
        )

        # ----------------------------------------------------
        # WAIT
        # ----------------------------------------------------

        print(
            "\nDad is now waiting..."
        )

        while True:

            response = await websocket.recv()

            data = json.loads(
                response
            )

            print(
                "\nReceived:"
            )

            print(
                json.dumps(
                    data,
                    indent=2
                )
            )

            if data.get(
                "type"
            ) == "message_status":

                print(
                    f"\n>>> "
                    f"{data.get('username')} "
                    f"status for message "
                    f"{data.get('message_id')}: "
                    f"{data.get('status')}"
                )

            elif data.get(
                "type"
            ) == "new_message":

                if data.get(
                    "sender_id"
                ) != user_id:

                    await acknowledge_message(
                        websocket,
                        data["message_id"]
                    )


if __name__ == "__main__":
    asyncio.run(main())