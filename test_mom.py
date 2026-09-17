import asyncio
import json
import websockets


SERVER_URL = "ws://localhost:8765"
USERNAME = "Mom"

OTHER_USERS = [
    "Dad",
    "Brother"
]


async def receive_until(
    websocket,
    expected_type
):
    """Wait until the expected response arrives."""

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
    """Wait until all required users exist."""

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
            "\nWaiting for "
            f"{required_names} to log in..."
        )

        await asyncio.sleep(1)


def build_user_map(users):
    """Create username -> user ID mapping."""

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
    """Find a conversation with exactly these participants."""

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
    """Get Mom's conversations."""

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
    """Reuse an existing conversation or create one."""

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

    print(
        f"\nCreating conversation: {name}"
    )

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

    conversation = response[
        "conversation"
    ]

    return conversation


async def get_history(
    websocket,
    conversation_id
):
    """Retrieve conversation history."""

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
    """Send a test message."""

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
    """Send delivery and read receipts."""

    print(
        f"\nMom -> delivered "
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
        f"Mom -> read "
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
    """
    Mark previously undelivered messages as delivered.

    This demonstrates offline-message recovery.
    """

    for message in messages:

        sender_id = message.get(
            "sender_id"
        )

        if sender_id == user_id:
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
                f"\nMom found offline message "
                f"{message_id}."
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

        # ====================================================
        # CONNECT
        # ====================================================

        connected = await receive_until(
            websocket,
            "connected"
        )

        print(
            "\nConnected:"
        )

        print(
            json.dumps(
                connected,
                indent=2
            )
        )

        # ====================================================
        # LOGIN
        # ====================================================

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
                "\nMom login failed."
            )

            return

        user_id = login[
            "user"
        ][
            "user_id"
        ]

        print(
            f"\nMom logged in "
            f"with ID {user_id}."
        )

        # ====================================================
        # WAIT FOR OTHER USERS
        # ====================================================

        users = await wait_for_users(
            websocket,
            OTHER_USERS
        )

        user_map = build_user_map(
            users
        )

        print(
            "\nUsers:"
        )

        print(
            json.dumps(
                user_map,
                indent=2
            )
        )

        dad_id = user_map["Dad"]
        brother_id = user_map["Brother"]

        # ====================================================
        # GET EXISTING CONVERSATIONS
        # ====================================================

        conversations = await get_conversations(
            websocket
        )

        # ====================================================
        # 1:1 WITH DAD
        # ====================================================

        mom_dad = await get_or_create_conversation(
            websocket,
            conversations,
            "Mom & Dad",
            [
                user_id,
                dad_id
            ]
        )

        # Refresh conversations.
        conversations = await get_conversations(
            websocket
        )

        # ====================================================
        # 1:1 WITH BROTHER
        # ====================================================

        mom_brother = await get_or_create_conversation(
            websocket,
            conversations,
            "Mom & Brother",
            [
                user_id,
                brother_id
            ]
        )

        # Refresh conversations.
        conversations = await get_conversations(
            websocket
        )

        # ====================================================
        # FAMILY GROUP
        # ====================================================

        family_group = await get_or_create_conversation(
            websocket,
            conversations,
            "Family Group",
            [
                user_id,
                dad_id,
                brother_id
            ]
        )

        print(
            "\n===================================="
        )

        print(
            "Mom conversations ready:"
        )

        print(
            f"1:1 Mom-Dad      = "
            f"{mom_dad['conversation_id']}"
        )

        print(
            f"1:1 Mom-Brother  = "
            f"{mom_brother['conversation_id']}"
        )

        print(
            f"Family Group     = "
            f"{family_group['conversation_id']}"
        )

        print(
            "===================================="
        )

        # ====================================================
        # RETRIEVE HISTORY
        # ====================================================

        for conversation in [
            mom_dad,
            mom_brother,
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

        # ====================================================
        # SEND 1:1 MESSAGE TO DAD
        # ====================================================

        print(
            "\nSending Mom -> Dad 1:1 message..."
        )

        message = await send_message(
            websocket,
            mom_dad["conversation_id"],
            "Hi Dad! This is a 1:1 message from Mom."
        )

        message_id = message[
            "message_id"
        ]

        print(
            f"\nMom sent message {message_id} "
            f"to Dad."
        )

        # ====================================================
        # SEND 1:1 MESSAGE TO BROTHER
        # ====================================================

        print(
            "\nSending Mom -> Brother 1:1 message..."
        )

        message = await send_message(
            websocket,
            mom_brother["conversation_id"],
            "Hi Brother! This is a 1:1 message from Mom."
        )

        print(
            f"\nMom sent message "
            f"{message['message_id']} "
            f"to Brother."
        )

        # ====================================================
        # SEND GROUP MESSAGE
        # ====================================================

        print(
            "\nSending Mom -> Family Group..."
        )

        message = await send_message(
            websocket,
            family_group["conversation_id"],
            "Hello Dad and Brother! - Mom"
        )

        print(
            f"\nMom sent group message "
            f"{message['message_id']}."
        )

        # ====================================================
        # WAIT FOR RECEIPTS
        # ====================================================

        print(
            "\nMom is now waiting for "
            "delivery/read receipts..."
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
                    "\n>>> "
                    f"{data.get('username')} "
                    f"status for message "
                    f"{data.get('message_id')}: "
                    f"{data.get('status')}"
                )

            elif data.get(
                "type"
            ) == "new_message":

                # Mom receives messages from Dad/Brother.
                sender_id = data.get(
                    "sender_id"
                )

                if sender_id != user_id:

                    await acknowledge_message(
                        websocket,
                        data["message_id"]
                    )


if __name__ == "__main__":
    asyncio.run(main())