import asyncio
import json
import os
from datetime import datetime

import websockets


HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 8765))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MESSAGES_FILE = os.path.join(BASE_DIR, "messages.json")


# Connected users:
# {
#     user_id: {
#         "username": username,
#         "websocket": websocket
#     }
# }
users = {}


# Registered users:
# {
#     user_id: {
#         "user_id": user_id,
#         "username": username,
#         "online": True/False
#     }
# }
registered_users = {}


# Conversations:
# {
#     conversation_id: {
#         "conversation_id": conversation_id,
#         "name": name,
#         "participants": [user_id, ...]
#     }
# }
conversations = {}


next_user_id = 1
next_conversation_id = 1
next_message_id = 1


def load_messages():
    """Load messages from messages.json."""

    if not os.path.exists(MESSAGES_FILE):
        return []

    try:
        with open(MESSAGES_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, list):
            return data

        return []

    except (json.JSONDecodeError, OSError):
        return []


def save_messages(messages):
    """Save all messages to messages.json."""

    with open(MESSAGES_FILE, "w", encoding="utf-8") as file:
        json.dump(
            messages,
            file,
            indent=2,
            ensure_ascii=False
        )


def save_message(
    conversation_id,
    sender_id,
    sender_username,
    content
):
    """Create and save a new message."""

    global next_message_id

    messages = load_messages()

    # Continue from the highest existing message ID.
    if messages:
        existing_ids = [
            message.get("message_id")
            for message in messages
            if isinstance(message.get("message_id"), int)
        ]

        if existing_ids:
            next_message_id = max(
                next_message_id,
                max(existing_ids) + 1
            )

    message = {
        "message_id": next_message_id,
        "conversation_id": conversation_id,
        "sender_id": sender_id,
        "sender_username": sender_username,
        "content": content,
        "timestamp": datetime.now().isoformat()
    }

    next_message_id += 1

    messages.append(message)
    save_messages(messages)

    return message


async def send_json(websocket, data):
    """Send a JSON object to a client."""

    await websocket.send(json.dumps(data))


async def send_error(
    websocket,
    message,
    code="INVALID_REQUEST"
):
    """Send a protocol error."""

    await send_json(
        websocket,
        {
            "type": "error",
            "code": code,
            "message": message
        }
    )


async def send_user_status(user_id, online):
    """Broadcast a user's online status."""

    user = registered_users.get(user_id)

    if user is None:
        return

    user["online"] = online

    message = {
        "type": "user_status",
        "user_id": user_id,
        "username": user["username"],
        "online": online
    }

    disconnected_users = []

    for connected_user_id, user_data in list(users.items()):
        try:
            await send_json(
                user_data["websocket"],
                message
            )

        except websockets.exceptions.ConnectionClosed:
            disconnected_users.append(connected_user_id)

    for disconnected_user_id in disconnected_users:
        users.pop(disconnected_user_id, None)


async def send_user_list():
    """Send all registered users to connected clients."""

    user_list = list(registered_users.values())

    message = {
        "type": "user_list",
        "users": user_list
    }

    disconnected_users = []

    for user_id, user_data in list(users.items()):
        try:
            await send_json(
                user_data["websocket"],
                message
            )

        except websockets.exceptions.ConnectionClosed:
            disconnected_users.append(user_id)

    for user_id in disconnected_users:
        users.pop(user_id, None)


def get_user_by_username(username):
    """Find a registered user by username."""

    for user in registered_users.values():
        if user["username"] == username:
            return user

    return None


def get_user_by_id(user_id):
    """Find a registered user by ID."""

    return registered_users.get(user_id)


def get_conversation(conversation_id):
    """Find a conversation by ID."""

    return conversations.get(conversation_id)


def user_is_participant(user_id, conversation):
    """Check whether a user belongs to a conversation."""

    return user_id in conversation["participants"]


async def handle_login(websocket, data):
    """Handle a login request."""

    global next_user_id

    username = data.get("username")

    if not isinstance(username, str):
        await send_error(
            websocket,
            "Username is required.",
            "INVALID_USERNAME"
        )
        return None

    username = username.strip()

    if not username:
        await send_error(
            websocket,
            "Username cannot be empty.",
            "INVALID_USERNAME"
        )
        return None

    existing_user = get_user_by_username(username)

    if existing_user is not None:

        if existing_user["online"]:
            await send_json(
                websocket,
                {
                    "type": "login_response",
                    "success": False,
                    "message": "Username is already online."
                }
            )
            return None

        user_id = existing_user["user_id"]
        registered_users[user_id]["online"] = True

    else:
        user_id = next_user_id
        next_user_id += 1

        registered_users[user_id] = {
            "user_id": user_id,
            "username": username,
            "online": True
        }

    users[user_id] = {
        "username": username,
        "websocket": websocket
    }

    await send_json(
        websocket,
        {
            "type": "login_response",
            "success": True,
            "user": registered_users[user_id]
        }
    )

    print(
        f"User '{username}' logged in with ID {user_id}."
    )

    await send_user_list()
    await send_user_status(user_id, True)

    return user_id


async def handle_get_users(user_id, websocket):
    """Return the list of registered users."""

    if user_id is None:
        await send_error(
            websocket,
            "You must log in first.",
            "NOT_AUTHENTICATED"
        )
        return

    await send_json(
        websocket,
        {
            "type": "user_list",
            "users": list(registered_users.values())
        }
    )


async def handle_get_conversations(user_id, websocket):
    """Return conversations that the user participates in."""

    if user_id is None:
        await send_error(
            websocket,
            "You must log in first.",
            "NOT_AUTHENTICATED"
        )
        return

    user_conversations = []

    for conversation in conversations.values():
        if user_is_participant(user_id, conversation):
            user_conversations.append(conversation)

    await send_json(
        websocket,
        {
            "type": "conversation_list",
            "conversations": user_conversations
        }
    )


async def handle_create_conversation(
    user_id,
    websocket,
    data
):
    """Create a new conversation."""

    global next_conversation_id

    if user_id is None:
        await send_error(
            websocket,
            "You must log in first.",
            "NOT_AUTHENTICATED"
        )
        return

    name = data.get("name")
    participant_ids = data.get("participant_ids")

    if not isinstance(participant_ids, list):
        await send_error(
            websocket,
            "participant_ids must be a list.",
            "INVALID_PARTICIPANTS"
        )
        return

    if not participant_ids:
        await send_error(
            websocket,
            "At least one participant is required.",
            "INVALID_PARTICIPANTS"
        )
        return

    if user_id not in participant_ids:
        participant_ids.append(user_id)

    cleaned_participants = []

    for participant_id in participant_ids:

        if not isinstance(participant_id, int):
            await send_error(
                websocket,
                "Participant IDs must be integers.",
                "INVALID_PARTICIPANTS"
            )
            return

        if participant_id not in registered_users:
            await send_error(
                websocket,
                f"User ID {participant_id} does not exist.",
                "INVALID_PARTICIPANTS"
            )
            return

        if participant_id not in cleaned_participants:
            cleaned_participants.append(participant_id)

    if isinstance(name, str):
        name = name.strip()

    if not name:
        participant_names = []

        for participant_id in cleaned_participants:
            participant = registered_users[participant_id]
            participant_names.append(participant["username"])

        name = " and ".join(participant_names)

    conversation = {
        "conversation_id": next_conversation_id,
        "name": name,
        "participants": cleaned_participants
    }

    conversations[next_conversation_id] = conversation
    next_conversation_id += 1

    await send_json(
        websocket,
        {
            "type": "create_conversation_response",
            "success": True,
            "conversation": conversation
        }
    )

    print(
        f"Conversation {conversation['conversation_id']} "
        f"created by user {user_id}."
    )


async def handle_get_messages(
    user_id,
    websocket,
    data
):
    """Return message history for a conversation."""

    if user_id is None:
        await send_error(
            websocket,
            "You must log in first.",
            "NOT_AUTHENTICATED"
        )
        return

    conversation_id = data.get("conversation_id")

    if not isinstance(conversation_id, int):
        await send_error(
            websocket,
            "conversation_id must be an integer.",
            "INVALID_CONVERSATION"
        )
        return

    conversation = get_conversation(conversation_id)

    if conversation is None:
        await send_error(
            websocket,
            "Conversation does not exist.",
            "CONVERSATION_NOT_FOUND"
        )
        return

    if not user_is_participant(user_id, conversation):
        await send_error(
            websocket,
            "You are not a participant in this conversation.",
            "ACCESS_DENIED"
        )
        return

    messages = load_messages()

    conversation_messages = []

    for message in messages:
        if message.get("conversation_id") == conversation_id:
            conversation_messages.append(message)

    await send_json(
        websocket,
        {
            "type": "message_history",
            "conversation_id": conversation_id,
            "messages": conversation_messages
        }
    )


async def handle_send_message(
    user_id,
    websocket,
    data
):
    """Create and broadcast a new conversation message."""

    if user_id is None:
        await send_error(
            websocket,
            "You must log in first.",
            "NOT_AUTHENTICATED"
        )
        return

    conversation_id = data.get("conversation_id")
    content = data.get("content")

    if not isinstance(conversation_id, int):
        await send_error(
            websocket,
            "conversation_id must be an integer.",
            "INVALID_CONVERSATION"
        )
        return

    if not isinstance(content, str):
        await send_error(
            websocket,
            "Message content is required.",
            "INVALID_CONTENT"
        )
        return

    content = content.strip()

    if not content:
        await send_error(
            websocket,
            "Message content cannot be empty.",
            "INVALID_CONTENT"
        )
        return

    conversation = get_conversation(conversation_id)

    if conversation is None:
        await send_error(
            websocket,
            "Conversation does not exist.",
            "CONVERSATION_NOT_FOUND"
        )
        return

    if not user_is_participant(user_id, conversation):
        await send_error(
            websocket,
            "You are not a participant in this conversation.",
            "ACCESS_DENIED"
        )
        return

    user = registered_users[user_id]

    message = save_message(
        conversation_id,
        user_id,
        user["username"],
        content
    )

    notification = {
        "type": "new_message",
        **message
    }

    disconnected_users = []

    for participant_id in conversation["participants"]:

        participant = users.get(participant_id)

        if participant is None:
            continue

        try:
            await send_json(
                participant["websocket"],
                notification
            )

        except websockets.exceptions.ConnectionClosed:
            disconnected_users.append(participant_id)

    for participant_id in disconnected_users:
        users.pop(participant_id, None)

    print(
        f"{user['username']} sent a message "
        f"in conversation {conversation_id}."
    )


async def handle_logout(user_id):
    """Log a user out."""

    if user_id is None:
        return

    user = registered_users.get(user_id)

    if user is None:
        return

    username = user["username"]

    users.pop(user_id, None)
    user["online"] = False

    print(
        f"User '{username}' logged out."
    )

    await send_user_status(user_id, False)
    await send_user_list()


async def handle_client(websocket):
    """Handle one WebSocket client connection."""

    print("Client connected!")

    user_id = None

    await send_json(
        websocket,
        {
            "type": "connected",
            "protocol_version": "1.0"
        }
    )

    try:

        async for raw_message in websocket:

            print(
                f"Received: {raw_message}"
            )

            try:
                data = json.loads(raw_message)

            except json.JSONDecodeError:
                await send_error(
                    websocket,
                    "Invalid JSON.",
                    "INVALID_JSON"
                )
                continue

            if not isinstance(data, dict):
                await send_error(
                    websocket,
                    "Message must be a JSON object.",
                    "INVALID_MESSAGE"
                )
                continue

            message_type = data.get("type")

            if message_type == "login":

                if user_id is not None:
                    await send_error(
                        websocket,
                        "You are already logged in.",
                        "ALREADY_AUTHENTICATED"
                    )
                    continue

                user_id = await handle_login(
                    websocket,
                    data
                )

            elif message_type == "get_users":

                await handle_get_users(
                    user_id,
                    websocket
                )

            elif message_type == "get_conversations":

                await handle_get_conversations(
                    user_id,
                    websocket
                )

            elif message_type == "create_conversation":

                await handle_create_conversation(
                    user_id,
                    websocket,
                    data
                )

            elif message_type == "get_messages":

                await handle_get_messages(
                    user_id,
                    websocket,
                    data
                )

            elif message_type == "send_message":

                await handle_send_message(
                    user_id,
                    websocket,
                    data
                )

            elif message_type == "logout":

                await handle_logout(user_id)
                user_id = None

            else:

                await send_error(
                    websocket,
                    "Unknown message type.",
                    "UNKNOWN_MESSAGE_TYPE"
                )

    except websockets.exceptions.ConnectionClosed:

        print("Client disconnected.")

    finally:

        if user_id is not None:

            user = registered_users.get(user_id)

            if user is not None:

                user["online"] = False
                users.pop(user_id, None)

                print(
                    f"User '{user['username']}' disconnected."
                )

                await send_user_status(
                    user_id,
                    False
                )

                await send_user_list()


async def main():
    """Start the WebSocket server."""

    print(
        f"Server running on ws://localhost:{PORT}"
    )

    async with websockets.serve(
        handle_client,
        HOST,
        PORT
    ):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())