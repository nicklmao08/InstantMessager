import asyncio
import json
import os
from datetime import datetime

import websockets


HOST = "0.0.0.0"
PORT = 8765

# Path to the JSON message storage file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MESSAGES_FILE = os.path.join(BASE_DIR, "messages.json")

# Currently connected users
# Example:
# {
#     "Alice": websocket,
#     "Bob": websocket
# }
users = {}


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


def save_message(sender, recipient, content):
    """Save a message to messages.json."""

    messages = load_messages()

    message = {
        "from": sender,
        "to": recipient,
        "content": content,
        "timestamp": datetime.now().isoformat()
    }

    messages.append(message)

    with open(MESSAGES_FILE, "w", encoding="utf-8") as file:
        json.dump(
            messages,
            file,
            indent=2,
            ensure_ascii=False
        )

    return message


async def send_json(websocket, data):
    """Send a JSON object to a client."""

    await websocket.send(json.dumps(data))


async def send_error(websocket, message):
    """Send an error message to a client."""

    await send_json(
        websocket,
        {
            "type": "error",
            "message": message
        }
    )


async def send_user_list():
    """Send the current online user list to everyone."""

    user_list = list(users.keys())

    message = {
        "type": "user_list",
        "users": user_list
    }

    disconnected_users = []

    for username, websocket in users.items():
        try:
            await send_json(websocket, message)

        except websockets.exceptions.ConnectionClosed:
            disconnected_users.append(username)

    for username in disconnected_users:
        if username in users:
            del users[username]


async def handle_login(websocket, data):
    """Handle a login request."""

    username = data.get("username")

    if not username:
        await send_error(
            websocket,
            "Username is required."
        )
        return None

    username = username.strip()

    if not username:
        await send_error(
            websocket,
            "Username cannot be empty."
        )
        return None

    if username in users:
        await send_json(
            websocket,
            {
                "type": "login_response",
                "status": "error",
                "message": "Username already exists."
            }
        )
        return None

    users[username] = websocket

    await send_json(
        websocket,
        {
            "type": "login_response",
            "status": "success",
            "username": username
        }
    )

    print(f"User '{username}' logged in.")

    await send_user_list()

    return username


async def handle_send_message(username, websocket, data):
    """Handle sending a message to another user."""

    if username is None:
        await send_error(
            websocket,
            "You must log in first."
        )
        return

    recipient = data.get("to")
    content = data.get("content")

    if not recipient:
        await send_error(
            websocket,
            "Recipient is required."
        )
        return

    if not content:
        await send_error(
            websocket,
            "Message content is required."
        )
        return

    recipient = recipient.strip()
    content = content.strip()

    if not recipient:
        await send_error(
            websocket,
            "Recipient cannot be empty."
        )
        return

    if not content:
        await send_error(
            websocket,
            "Message content cannot be empty."
        )
        return

    if recipient not in users:
        await send_error(
            websocket,
            f"User '{recipient}' is not online."
        )
        return

    # Save message to JSON
    saved_message = save_message(
        username,
        recipient,
        content
    )

    # Create message for recipient
    chat_message = {
        "type": "message",
        "from": username,
        "to": recipient,
        "content": content,
        "timestamp": saved_message["timestamp"]
    }

    try:
        await send_json(
            users[recipient],
            chat_message
        )

        print(
            f"{username} -> {recipient}: {content}"
        )

    except websockets.exceptions.ConnectionClosed:
        await send_error(
            websocket,
            f"User '{recipient}' disconnected."
        )


async def handle_get_history(username, websocket, data):
    """Send conversation history between two users."""

    if username is None:
        await send_error(
            websocket,
            "You must log in first."
        )
        return

    other_user = data.get("with")

    if not other_user:
        await send_error(
            websocket,
            "Username is required."
        )
        return

    other_user = other_user.strip()

    if not other_user:
        await send_error(
            websocket,
            "Username cannot be empty."
        )
        return

    messages = load_messages()

    conversation = []

    for message in messages:

        is_sent_message = (
            message.get("from") == username
            and message.get("to") == other_user
        )

        is_received_message = (
            message.get("from") == other_user
            and message.get("to") == username
        )

        if is_sent_message or is_received_message:
            conversation.append(message)

    await send_json(
        websocket,
        {
            "type": "history",
            "with": other_user,
            "messages": conversation
        }
    )

    print(
        f"History requested: {username} <-> {other_user}"
    )


async def handle_logout(username):
    """Remove a user from the online users list."""

    if username is None:
        return

    if username in users:

        del users[username]

        print(
            f"User '{username}' logged out."
        )

        await send_user_list()


async def handle_client(websocket):
    """Handle one WebSocket client connection."""

    print("Client connected!")

    username = None

    try:

        async for raw_message in websocket:

            print(
                f"Received: {raw_message}"
            )

            # Convert JSON string to Python dictionary
            try:
                data = json.loads(raw_message)

            except json.JSONDecodeError:

                await send_error(
                    websocket,
                    "Invalid JSON."
                )

                continue

            # Make sure JSON is an object
            if not isinstance(data, dict):

                await send_error(
                    websocket,
                    "Message must be a JSON object."
                )

                continue

            message_type = data.get("type")

            # =========================
            # LOGIN
            # =========================

            if message_type == "login":

                if username is not None:

                    await send_error(
                        websocket,
                        "You are already logged in."
                    )

                    continue

                username = await handle_login(
                    websocket,
                    data
                )

            # =========================
            # SEND MESSAGE
            # =========================

            elif message_type == "send_message":

                await handle_send_message(
                    username,
                    websocket,
                    data
                )

            # =========================
            # GET HISTORY
            # =========================

            elif message_type == "get_history":

                await handle_get_history(
                    username,
                    websocket,
                    data
                )

            # =========================
            # LOGOUT
            # =========================

            elif message_type == "logout":

                await handle_logout(username)

                username = None

                await websocket.close()

                break

            # =========================
            # UNKNOWN MESSAGE TYPE
            # =========================

            else:

                await send_error(
                    websocket,
                    "Unknown message type."
                )

    except websockets.exceptions.ConnectionClosed:

        print("Client disconnected.")

    finally:

        # Remove user if connection closes unexpectedly
        if username is not None and username in users:

            del users[username]

            print(
                f"User '{username}' disconnected."
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