import asyncio
import json
import os
from datetime import datetime

import websockets


HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 8765))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MESSAGES_FILE = os.path.join(BASE_DIR, "messages.json")
CONVERSATIONS_FILE = os.path.join(BASE_DIR, "conversations.json")


# ============================================================
# IN-MEMORY SERVER STATE
# ============================================================

# Currently connected users:
#
# {
#     user_id: {
#         "username": username,
#         "websocket": websocket
#     }
# }

users = {}


# Registered users:
#
# {
#     user_id: {
#         "user_id": user_id,
#         "username": username,
#         "online": True / False
#     }
# }

registered_users = {}


# Conversations:
#
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


# ============================================================
# CONVERSATION STORAGE
# ============================================================

def load_conversations():
    """Load conversations from conversations.json."""
    global conversations, next_conversation_id

    if not os.path.exists(CONVERSATIONS_FILE):
        return

    try:
        with open(CONVERSATIONS_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, list):
            conversations = {
                item["conversation_id"]: item
                for item in data
            }

            if conversations:
                next_conversation_id = max(conversations.keys()) + 1

    except (json.JSONDecodeError, OSError, ValueError):
        conversations = {}


def save_conversations():
    """Save conversations to conversations.json."""
    with open(CONVERSATIONS_FILE, "w", encoding="utf-8") as file:
        json.dump(conversations, file, indent=4)


# ============================================================
# MESSAGE STORAGE
# ============================================================

def load_messages():
    """Load messages from messages.json."""

    if not os.path.exists(MESSAGES_FILE):
        return []

    try:
        with open(
            MESSAGES_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if isinstance(data, list):
            return data

        return []

    except (json.JSONDecodeError, OSError):
        return []


def save_messages(messages):
    """Save all messages to messages.json."""

    with open(
        MESSAGES_FILE,
        "w",
        encoding="utf-8"
    ) as file:

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
    content,
    participant_ids
):
    """Create and save a new message."""

    global next_message_id

    messages = load_messages()

    # Continue from the highest existing message ID.
    existing_ids = [
        message.get("message_id")
        for message in messages
        if isinstance(
            message.get("message_id"),
            int
        )
    ]

    if existing_ids:
        next_message_id = max(
            next_message_id,
            max(existing_ids) + 1
        )

    # Every recipient starts as "sent".
    # The sender does not receive a receipt for their own message.
    receipts = {}

    for participant_id in participant_ids:

        if participant_id != sender_id:

            receipts[str(participant_id)] = "sent"

    message = {
        "message_id": next_message_id,
        "conversation_id": conversation_id,
        "sender_id": sender_id,
        "sender_username": sender_username,
        "content": content,
        "timestamp": datetime.now().isoformat(),
        "receipts": receipts
    }

    next_message_id += 1

    messages.append(message)

    save_messages(messages)

    return message


def find_message_by_id(message_id):
    """Find a message by message ID."""

    messages = load_messages()

    for message in messages:

        if message.get("message_id") == message_id:
            return message

    return None


def update_message_receipt(
    message_id,
    user_id,
    new_status
):
    """
    Update a recipient's message receipt.

    Receipt progression:

        sent -> delivered -> read

    Receipts cannot move backwards.
    """

    messages = load_messages()

    for message in messages:

        if message.get("message_id") != message_id:
            continue

        if "receipts" not in message:
            message["receipts"] = {}

        user_key = str(user_id)

        current_status = message["receipts"].get(
            user_key,
            "sent"
        )

        # A read message cannot change.
        if current_status == "read":
            return message, False

        # Only delivered/read are valid updates.
        if new_status not in (
            "delivered",
            "read"
        ):
            return message, False

        if new_status == "delivered":

            if current_status == "sent":

                message["receipts"][user_key] = "delivered"

            else:
                return message, False

        elif new_status == "read":

            message["receipts"][user_key] = "read"

        save_messages(messages)

        return message, True

    return None, False


# ============================================================
# GENERAL HELPERS
# ============================================================

async def send_json(websocket, data):
    """Send JSON data to a websocket."""

    await websocket.send(
        json.dumps(data)
    )


async def send_error(
    websocket,
    message,
    code="INVALID_REQUEST"
):
    """Send an error response."""

    await send_json(
        websocket,
        {
            "type": "error",
            "code": code,
            "message": message
        }
    )


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

    return conversations.get(
        conversation_id
    )


def user_is_participant(
    user_id,
    conversation
):
    """Check whether a user belongs to a conversation."""

    return user_id in conversation["participants"]


def conversation_has_same_participants(
    conversation,
    participant_ids
):
    """Check whether a conversation has exactly these participants."""

    existing = set(
        conversation.get(
            "participants",
            []
        )
    )

    requested = set(
        participant_ids
    )

    return existing == requested


def find_conversation_by_participants(
    participant_ids
):
    """
    Find an existing conversation with exactly
    the requested participants.
    """

    requested = set(participant_ids)

    for conversation in conversations.values():

        existing = set(
            conversation.get(
                "participants",
                []
            )
        )

        if existing == requested:
            return conversation

    return None


async def notify_message_sender(
    message,
    recipient_id,
    status
):
    """Notify the sender that a recipient updated a receipt."""

    sender_id = message.get(
        "sender_id"
    )

    if sender_id is None:
        return

    sender = users.get(sender_id)

    if sender is None:
        return

    recipient = registered_users.get(
        recipient_id
    )

    if recipient is None:
        return

    notification = {
        "type": "message_status",
        "message_id": message["message_id"],
        "conversation_id": message["conversation_id"],
        "user_id": recipient_id,
        "username": recipient["username"],
        "status": status
    }

    try:

        await send_json(
            sender["websocket"],
            notification
        )

    except websockets.exceptions.ConnectionClosed:

        users.pop(
            sender_id,
            None
        )


# ============================================================
# USER STATUS
# ============================================================

async def send_user_status(
    user_id,
    online
):
    """Broadcast a user's online/offline status."""

    user = registered_users.get(
        user_id
    )

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

    for connected_user_id, user_data in list(
        users.items()
    ):

        try:

            await send_json(
                user_data["websocket"],
                message
            )

        except websockets.exceptions.ConnectionClosed:

            disconnected_users.append(
                connected_user_id
            )

    for disconnected_user_id in disconnected_users:

        users.pop(
            disconnected_user_id,
            None
        )


async def send_user_list():
    """Broadcast the current registered-user list."""

    message = {
        "type": "user_list",
        "users": list(
            registered_users.values()
        )
    }

    disconnected_users = []

    for user_id, user_data in list(
        users.items()
    ):

        try:

            await send_json(
                user_data["websocket"],
                message
            )

        except websockets.exceptions.ConnectionClosed:

            disconnected_users.append(
                user_id
            )

    for user_id in disconnected_users:

        users.pop(
            user_id,
            None
        )


# ============================================================
# LOGIN
# ============================================================

async def handle_login(
    websocket,
    data
):
    """Handle a login request."""

    global next_user_id

    username = data.get(
        "username"
    )

    if not isinstance(
        username,
        str
    ):

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

    existing_user = get_user_by_username(
        username
    )

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

        existing_user["online"] = True

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
        f"User '{username}' "
        f"logged in with ID {user_id}."
    )

    await send_user_list()

    await send_user_status(
        user_id,
        True
    )

    return user_id


# ============================================================
# GET USERS
# ============================================================

async def handle_get_users(
    user_id,
    websocket
):
    """Return all registered users."""

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
            "users": list(
                registered_users.values()
            )
        }
    )


# ============================================================
# GET CONVERSATIONS
# ============================================================

async def handle_get_conversations(
    user_id,
    websocket
):
    """Return conversations for the logged-in user."""

    if user_id is None:

        await send_error(
            websocket,
            "You must log in first.",
            "NOT_AUTHENTICATED"
        )

        return

    user_conversations = []

    for conversation in conversations.values():

        if user_is_participant(
            user_id,
            conversation
        ):

            user_conversations.append(
                conversation
            )

    await send_json(
        websocket,
        {
            "type": "conversation_list",
            "conversations": user_conversations
        }
    )


# ============================================================
# CREATE CONVERSATION
# ============================================================

async def handle_create_conversation(
    user_id,
    websocket,
    data
):
    """
    Create either a 1:1 or group conversation.

    All authenticated users have the same permission.
    """

    global next_conversation_id

    if user_id is None:

        await send_error(
            websocket,
            "You must log in first.",
            "NOT_AUTHENTICATED"
        )

        return

    name = data.get(
        "name"
    )

    participant_ids = data.get(
        "participant_ids"
    )

    if not isinstance(
        participant_ids,
        list
    ):

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

    # Always include creator.
    if user_id not in participant_ids:

        participant_ids.append(
            user_id
        )

    cleaned_participants = []

    for participant_id in participant_ids:

        if not isinstance(
            participant_id,
            int
        ):

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

            cleaned_participants.append(
                participant_id
            )

    # Prevent duplicate conversations.
    existing = find_conversation_by_participants(
        cleaned_participants
    )

    if existing is not None:

        await send_json(
            websocket,
            {
                "type": "create_conversation_response",
                "success": True,
                "existing": True,
                "conversation": existing
            }
        )

        print(
            f"User {user_id} requested an existing "
            f"conversation {existing['conversation_id']}."
        )

        return

    # Generate a default name if necessary.
    if isinstance(
        name,
        str
    ):

        name = name.strip()

    if not name:

        participant_names = []

        for participant_id in cleaned_participants:

            participant = registered_users[
                participant_id
            ]

            participant_names.append(
                participant["username"]
            )

        if len(cleaned_participants) == 2:

            name = " & ".join(
                participant_names
            )

        else:

            name = "Group: " + ", ".join(
                participant_names
            )

    conversation = {
        "conversation_id": next_conversation_id,
        "name": name,
        "participants": cleaned_participants
    }

    conversations[
        next_conversation_id
    ] = conversation

    next_conversation_id += 1

    await send_json(
        websocket,
        {
            "type": "create_conversation_response",
            "success": True,
            "existing": False,
            "conversation": conversation
        }
    )

    print(
        f"Conversation "
        f"{conversation['conversation_id']} "
        f"created by user {user_id}."
    )


# ============================================================
# GET MESSAGE HISTORY
# ============================================================

async def handle_get_messages(
    user_id,
    websocket,
    data
):
    """Return message history."""

    if user_id is None:

        await send_error(
            websocket,
            "You must log in first.",
            "NOT_AUTHENTICATED"
        )

        return

    conversation_id = data.get(
        "conversation_id"
    )

    if not isinstance(
        conversation_id,
        int
    ):

        await send_error(
            websocket,
            "conversation_id must be an integer.",
            "INVALID_CONVERSATION"
        )

        return

    conversation = get_conversation(
        conversation_id
    )

    if conversation is None:

        await send_error(
            websocket,
            "Conversation does not exist.",
            "CONVERSATION_NOT_FOUND"
        )

        return

    if not user_is_participant(
        user_id,
        conversation
    ):

        await send_error(
            websocket,
            "You are not a participant in this conversation.",
            "ACCESS_DENIED"
        )

        return

    messages = load_messages()

    conversation_messages = []

    for message in messages:

        if message.get(
            "conversation_id"
        ) != conversation_id:

            continue

        # Compatibility with older messages.
        if "receipts" not in message:

            message["receipts"] = {}

        conversation_messages.append(
            message
        )

    await send_json(
        websocket,
        {
            "type": "message_history",
            "conversation_id": conversation_id,
            "messages": conversation_messages
        }
    )


# ============================================================
# SEND MESSAGE
# ============================================================

async def handle_send_message(
    user_id,
    websocket,
    data
):
    """Create and broadcast a message."""

    if user_id is None:

        await send_error(
            websocket,
            "You must log in first.",
            "NOT_AUTHENTICATED"
        )

        return

    conversation_id = data.get(
        "conversation_id"
    )

    content = data.get(
        "content"
    )

    if not isinstance(
        conversation_id,
        int
    ):

        await send_error(
            websocket,
            "conversation_id must be an integer.",
            "INVALID_CONVERSATION"
        )

        return

    if not isinstance(
        content,
        str
    ):

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

    conversation = get_conversation(
        conversation_id
    )

    if conversation is None:

        await send_error(
            websocket,
            "Conversation does not exist.",
            "CONVERSATION_NOT_FOUND"
        )

        return

    if not user_is_participant(
        user_id,
        conversation
    ):

        await send_error(
            websocket,
            "You are not a participant in this conversation.",
            "ACCESS_DENIED"
        )

        return

    user = registered_users[
        user_id
    ]

    message = save_message(
        conversation_id,
        user_id,
        user["username"],
        content,
        conversation["participants"]
    )

    notification = {
        "type": "new_message",
        **message
    }

    disconnected_users = []

    for participant_id in conversation["participants"]:

        participant = users.get(
            participant_id
        )

        # Offline users do not receive the live message.
        # It remains stored with receipt = sent.
        if participant is None:
            continue

        try:

            await send_json(
                participant["websocket"],
                notification
            )

        except websockets.exceptions.ConnectionClosed:

            disconnected_users.append(
                participant_id
            )

    for participant_id in disconnected_users:

        users.pop(
            participant_id,
            None
        )

    print(
        f"{user['username']} sent a message "
        f"in conversation {conversation_id}."
    )


# ============================================================
# DELIVERY RECEIPT
# ============================================================

async def handle_message_delivered(
    user_id,
    websocket,
    data
):
    """Handle a recipient marking a message as delivered."""

    if user_id is None:

        await send_error(
            websocket,
            "You must log in first.",
            "NOT_AUTHENTICATED"
        )

        return

    message_id = data.get(
        "message_id"
    )

    if not isinstance(
        message_id,
        int
    ):

        await send_error(
            websocket,
            "message_id must be an integer.",
            "INVALID_MESSAGE"
        )

        return

    message = find_message_by_id(
        message_id
    )

    if message is None:

        await send_error(
            websocket,
            "Message does not exist.",
            "MESSAGE_NOT_FOUND"
        )

        return

    conversation = get_conversation(
        message.get("conversation_id")
    )

    if conversation is None:

        await send_error(
            websocket,
            "Conversation does not exist.",
            "CONVERSATION_NOT_FOUND"
        )

        return

    if not user_is_participant(
        user_id,
        conversation
    ):

        await send_error(
            websocket,
            "You are not a participant in this conversation.",
            "ACCESS_DENIED"
        )

        return

    if user_id == message.get(
        "sender_id"
    ):

        await send_error(
            websocket,
            "The sender cannot acknowledge delivery.",
            "INVALID_RECEIPT"
        )

        return

    # Make sure this recipient belongs to this message.
    receipts = message.get(
        "receipts",
        {}
    )

    if str(user_id) not in receipts:

        await send_error(
            websocket,
            "This message was not sent to you.",
            "INVALID_RECEIPT"
        )

        return

    updated_message, changed = update_message_receipt(
        message_id,
        user_id,
        "delivered"
    )

    if changed:

        await notify_message_sender(
            updated_message,
            user_id,
            "delivered"
        )

        print(
            f"User {user_id} received "
            f"message {message_id}."
        )


# ============================================================
# READ RECEIPT
# ============================================================

async def handle_message_read(
    user_id,
    websocket,
    data
):
    """Handle a recipient marking a message as read."""

    if user_id is None:

        await send_error(
            websocket,
            "You must log in first.",
            "NOT_AUTHENTICATED"
        )

        return

    message_id = data.get(
        "message_id"
    )

    if not isinstance(
        message_id,
        int
    ):

        await send_error(
            websocket,
            "message_id must be an integer.",
            "INVALID_MESSAGE"
        )

        return

    message = find_message_by_id(
        message_id
    )

    if message is None:

        await send_error(
            websocket,
            "Message does not exist.",
            "MESSAGE_NOT_FOUND"
        )

        return

    conversation = get_conversation(
        message.get("conversation_id")
    )

    if conversation is None:

        await send_error(
            websocket,
            "Conversation does not exist.",
            "CONVERSATION_NOT_FOUND"
        )

        return

    if not user_is_participant(
        user_id,
        conversation
    ):

        await send_error(
            websocket,
            "You are not a participant in this conversation.",
            "ACCESS_DENIED"
        )

        return

    if user_id == message.get(
        "sender_id"
    ):

        await send_error(
            websocket,
            "The sender cannot acknowledge the message as read.",
            "INVALID_RECEIPT"
        )

        return

    receipts = message.get(
        "receipts",
        {}
    )

    if str(user_id) not in receipts:

        await send_error(
            websocket,
            "This message was not sent to you.",
            "INVALID_RECEIPT"
        )

        return

    updated_message, changed = update_message_receipt(
        message_id,
        user_id,
        "read"
    )

    if changed:

        await notify_message_sender(
            updated_message,
            user_id,
            "read"
        )

        print(
            f"User {user_id} read "
            f"message {message_id}."
        )


# ============================================================
# LOGOUT
# ============================================================

async def handle_logout(
    user_id
):
    """Log a user out."""

    if user_id is None:
        return

    user = registered_users.get(
        user_id
    )

    if user is None:
        return

    username = user["username"]

    users.pop(
        user_id,
        None
    )

    user["online"] = False

    print(
        f"User '{username}' logged out."
    )

    await send_user_status(
        user_id,
        False
    )

    await send_user_list()


# ============================================================
# CLIENT CONNECTION
# ============================================================

async def handle_client(
    websocket
):
    """Handle one WebSocket connection."""

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

                data = json.loads(
                    raw_message
                )

            except json.JSONDecodeError:

                await send_error(
                    websocket,
                    "Invalid JSON.",
                    "INVALID_JSON"
                )

                continue

            if not isinstance(
                data,
                dict
            ):

                await send_error(
                    websocket,
                    "Message must be a JSON object.",
                    "INVALID_MESSAGE"
                )

                continue

            message_type = data.get(
                "type"
            )

            # ------------------------------------------------
            # LOGIN
            # ------------------------------------------------

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

            # ------------------------------------------------
            # GET USERS
            # ------------------------------------------------

            elif message_type == "get_users":

                await handle_get_users(
                    user_id,
                    websocket
                )

            # ------------------------------------------------
            # GET CONVERSATIONS
            # ------------------------------------------------

            elif message_type == "get_conversations":

                await handle_get_conversations(
                    user_id,
                    websocket
                )

            # ------------------------------------------------
            # CREATE CONVERSATION
            # ------------------------------------------------

            elif message_type == "create_conversation":

                await handle_create_conversation(
                    user_id,
                    websocket,
                    data
                )

            # ------------------------------------------------
            # GET HISTORY
            # ------------------------------------------------

            elif message_type == "get_messages":

                await handle_get_messages(
                    user_id,
                    websocket,
                    data
                )

            # ------------------------------------------------
            # SEND MESSAGE
            # ------------------------------------------------

            elif message_type == "send_message":

                await handle_send_message(
                    user_id,
                    websocket,
                    data
                )

            # ------------------------------------------------
            # DELIVERY
            # ------------------------------------------------

            elif message_type == "message_delivered":

                await handle_message_delivered(
                    user_id,
                    websocket,
                    data
                )

            # ------------------------------------------------
            # READ
            # ------------------------------------------------

            elif message_type == "message_read":

                await handle_message_read(
                    user_id,
                    websocket,
                    data
                )

            # ------------------------------------------------
            # LOGOUT
            # ------------------------------------------------

            elif message_type == "logout":

                await handle_logout(
                    user_id
                )

                user_id = None

            # ------------------------------------------------
            # UNKNOWN
            # ------------------------------------------------

            else:

                await send_error(
                    websocket,
                    "Unknown message type.",
                    "UNKNOWN_MESSAGE_TYPE"
                )

    except websockets.exceptions.ConnectionClosed:

        print(
            "Client disconnected."
        )

    finally:

        if user_id is not None:

            user = registered_users.get(
                user_id
            )

            if user is not None:

                user["online"] = False

                users.pop(
                    user_id,
                    None
                )

                print(
                    f"User '{user['username']}' "
                    f"disconnected."
                )

                await send_user_status(
                    user_id,
                    False
                )

                await send_user_list()


# ============================================================
# MAIN
# ============================================================

async def main():
    """Start the WebSocket server."""

    print(
        f"Server running on ws://localhost:{PORT}"
    )

    load_conversations()

    async with websockets.serve(
        handle_client,
        HOST,
        PORT,
        ping_interval=20,
        ping_timeout=20
    ):

        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())