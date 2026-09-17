"""Automated integration tests for InstantMessager's WebSocket server.

Run with:
    python3 -m unittest -v test_server_automated.py
"""

import asyncio
import json
import os
import tempfile
import unittest

import websockets

import server


async def recv_json(ws, timeout=1.5):
    """Receive one JSON message."""
    raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
    return json.loads(raw)


async def recv_until_type(ws, expected_type, timeout=2.0):
    """Keep receiving until the expected message type appears."""
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    seen = []

    while loop.time() < deadline:
        remaining = max(0.01, deadline - loop.time())
        msg = await recv_json(ws, timeout=remaining)
        seen.append(msg)

        if msg.get("type") == expected_type:
            return msg

    raise AssertionError(
        f"Did not receive type={expected_type!r}. Messages seen: {seen}"
    )


class InstantMessagerServerTests(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        """Prepare a clean server before every test."""

        server.users.clear()
        server.registered_users.clear()
        server.conversations.clear()

        server.next_user_id = 1
        server.next_conversation_id = 1
        server.next_message_id = 1

        # Create temporary message storage.
        self.tempdir = tempfile.TemporaryDirectory()

        self.original_messages_file = server.MESSAGES_FILE

        server.MESSAGES_FILE = os.path.join(
            self.tempdir.name,
            "messages.json"
        )

        with open(server.MESSAGES_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)

        # Start test server on a free port.
        self.ws_server = await websockets.serve(
            server.handle_client,
            "127.0.0.1",
            0
        )

        port = self.ws_server.sockets[0].getsockname()[1]

        self.uri = f"ws://127.0.0.1:{port}"

    async def asyncTearDown(self):
        """Stop the test server after every test."""

        self.ws_server.close()

        await self.ws_server.wait_closed()

        server.MESSAGES_FILE = self.original_messages_file

        self.tempdir.cleanup()

    async def connect(self):
        """Connect a test client."""

        ws = await websockets.connect(self.uri)

        connected = await recv_json(ws)

        self.assertEqual(
            connected["type"],
            "connected"
        )

        self.assertEqual(
            connected["protocol_version"],
            "1.0"
        )

        return ws

    async def login(self, ws, username):
        """Login a test user."""

        await ws.send(json.dumps({
            "type": "login",
            "username": username
        }))

        response = await recv_until_type(
            ws,
            "login_response"
        )

        return response

    async def drain(self, ws):
        """Remove queued messages."""

        while True:

            try:

                await recv_json(
                    ws,
                    timeout=0.03
                )

            except (
                asyncio.TimeoutError,
                websockets.exceptions.ConnectionClosed
            ):

                break

    async def make_two_users_and_conversation(self):
        """Create Alice, Bob and a conversation."""

        alice_ws = await self.connect()

        alice_login = await self.login(
            alice_ws,
            "Alice"
        )

        self.assertTrue(
            alice_login["success"]
        )

        alice_id = alice_login["user"]["user_id"]

        await self.drain(alice_ws)

        bob_ws = await self.connect()

        bob_login = await self.login(
            bob_ws,
            "Bob"
        )

        self.assertTrue(
            bob_login["success"]
        )

        bob_id = bob_login["user"]["user_id"]

        await self.drain(alice_ws)
        await self.drain(bob_ws)

        # Alice creates a conversation with Bob.
        await alice_ws.send(json.dumps({

            "type": "create_conversation",

            "name": "Alice and Bob",

            "participant_ids": [
                alice_id,
                bob_id
            ]
        }))

        created = await recv_until_type(
            alice_ws,
            "create_conversation_response"
        )

        self.assertTrue(
            created["success"]
        )

        conversation_id = (
            created["conversation"]["conversation_id"]
        )

        return (
            alice_ws,
            bob_ws,
            alice_id,
            bob_id,
            conversation_id
        )

    # -------------------------------------------------
    # TEST 1
    # -------------------------------------------------

    async def test_01_connection_handshake(self):

        ws = await self.connect()

        await ws.close()

    # -------------------------------------------------
    # TEST 2
    # -------------------------------------------------

    async def test_02_valid_login_and_user_list(self):

        ws = await self.connect()

        response = await self.login(
            ws,
            "Alice"
        )

        self.assertTrue(
            response["success"]
        )

        self.assertEqual(
            response["user"]["username"],
            "Alice"
        )

        self.assertTrue(
            response["user"]["online"]
        )

        user_list = await recv_until_type(
            ws,
            "user_list"
        )

        self.assertEqual(
            len(user_list["users"]),
            1
        )

        self.assertEqual(
            user_list["users"][0]["username"],
            "Alice"
        )

        await ws.close()

    # -------------------------------------------------
    # TEST 3
    # -------------------------------------------------

    async def test_03_empty_username_is_rejected(self):

        ws = await self.connect()

        await ws.send(json.dumps({

            "type": "login",

            "username": "   "
        }))

        response = await recv_until_type(
            ws,
            "error"
        )

        self.assertEqual(
            response["code"],
            "INVALID_USERNAME"
        )

        await ws.close()

    # -------------------------------------------------
    # TEST 4
    # -------------------------------------------------

    async def test_04_duplicate_online_username_is_rejected(self):

        alice1 = await self.connect()

        first = await self.login(
            alice1,
            "Alice"
        )

        self.assertTrue(
            first["success"]
        )

        await self.drain(alice1)

        alice2 = await self.connect()

        second = await self.login(
            alice2,
            "Alice"
        )

        self.assertFalse(
            second["success"]
        )

        self.assertIn(
            "already online",
            second["message"]
        )

        await alice1.close()
        await alice2.close()

    # -------------------------------------------------
    # TEST 5
    # -------------------------------------------------

    async def test_05_unauthenticated_request_is_rejected(self):

        ws = await self.connect()

        await ws.send(json.dumps({

            "type": "get_users"
        }))

        response = await recv_until_type(
            ws,
            "error"
        )

        self.assertEqual(
            response["code"],
            "NOT_AUTHENTICATED"
        )

        await ws.close()

    # -------------------------------------------------
    # TEST 6
    # -------------------------------------------------

    async def test_06_create_conversation_and_list_it(self):

        (
            alice,
            bob,
            alice_id,
            bob_id,
            conv_id

        ) = await self.make_two_users_and_conversation()

        await bob.send(json.dumps({

            "type": "get_conversations"
        }))

        response = await recv_until_type(
            bob,
            "conversation_list"
        )

        ids = [

            c["conversation_id"]

            for c in response["conversations"]
        ]

        self.assertIn(
            conv_id,
            ids
        )

        conversation = next(

            c for c in response["conversations"]

            if c["conversation_id"] == conv_id
        )

        self.assertEqual(

            set(conversation["participants"]),

            {
                alice_id,
                bob_id
            }
        )

        await alice.close()
        await bob.close()

    # -------------------------------------------------
    # TEST 7
    # -------------------------------------------------

    async def test_07_message_is_broadcast_and_persisted(self):

        (
            alice,
            bob,
            alice_id,
            _,
            conv_id

        ) = await self.make_two_users_and_conversation()

        await alice.send(json.dumps({

            "type": "send_message",

            "conversation_id": conv_id,

            "content": "Hello Bob!"
        }))

        alice_msg = await recv_until_type(
            alice,
            "new_message"
        )

        bob_msg = await recv_until_type(
            bob,
            "new_message"
        )

        self.assertEqual(
            alice_msg["content"],
            "Hello Bob!"
        )

        self.assertEqual(
            bob_msg["content"],
            "Hello Bob!"
        )

        self.assertEqual(
            bob_msg["sender_id"],
            alice_id
        )

        self.assertEqual(
            alice_msg["message_id"],
            bob_msg["message_id"]
        )

        # Check messages.json storage.
        stored = server.load_messages()

        self.assertEqual(
            len(stored),
            1
        )

        self.assertEqual(
            stored[0]["content"],
            "Hello Bob!"
        )

        self.assertEqual(
            stored[0]["conversation_id"],
            conv_id
        )

        await alice.close()
        await bob.close()

    # -------------------------------------------------
    # TEST 8
    # -------------------------------------------------

    async def test_08_message_history_returns_saved_messages(self):

        (
            alice,
            bob,
            _,
            _,
            conv_id

        ) = await self.make_two_users_and_conversation()

        await alice.send(json.dumps({

            "type": "send_message",

            "conversation_id": conv_id,

            "content": "History test"
        }))

        await recv_until_type(
            alice,
            "new_message"
        )

        await recv_until_type(
            bob,
            "new_message"
        )

        await bob.send(json.dumps({

            "type": "get_messages",

            "conversation_id": conv_id
        }))

        history = await recv_until_type(
            bob,
            "message_history"
        )

        self.assertEqual(
            history["conversation_id"],
            conv_id
        )

        self.assertEqual(
            len(history["messages"]),
            1
        )

        self.assertEqual(
            history["messages"][0]["content"],
            "History test"
        )

        await alice.close()
        await bob.close()

    # -------------------------------------------------
    # TEST 9
    # -------------------------------------------------

    async def test_09_empty_message_is_rejected(self):

        (
            alice,
            bob,
            _,
            _,
            conv_id

        ) = await self.make_two_users_and_conversation()

        await alice.send(json.dumps({

            "type": "send_message",

            "conversation_id": conv_id,

            "content": "   "
        }))

        response = await recv_until_type(
            alice,
            "error"
        )

        self.assertEqual(
            response["code"],
            "INVALID_CONTENT"
        )

        self.assertEqual(
            server.load_messages(),
            []
        )

        await alice.close()
        await bob.close()

    # -------------------------------------------------
    # TEST 10
    # -------------------------------------------------

    async def test_10_nonparticipant_cannot_read_or_send(self):

        (
            alice,
            bob,
            _,
            _,
            conv_id

        ) = await self.make_two_users_and_conversation()

        charlie = await self.connect()

        charlie_login = await self.login(
            charlie,
            "Charlie"
        )

        self.assertTrue(
            charlie_login["success"]
        )

        await self.drain(alice)
        await self.drain(bob)
        await self.drain(charlie)

        # Charlie tries to read the conversation.
        await charlie.send(json.dumps({

            "type": "get_messages",

            "conversation_id": conv_id
        }))

        read_error = await recv_until_type(
            charlie,
            "error"
        )

        self.assertEqual(
            read_error["code"],
            "ACCESS_DENIED"
        )

        # Charlie tries to send into the conversation.
        await charlie.send(json.dumps({

            "type": "send_message",

            "conversation_id": conv_id,

            "content": "I should not be allowed"
        }))

        send_error = await recv_until_type(
            charlie,
            "error"
        )

        self.assertEqual(
            send_error["code"],
            "ACCESS_DENIED"
        )

        await alice.close()
        await bob.close()
        await charlie.close()

    # -------------------------------------------------
    # TEST 11
    # -------------------------------------------------

    async def test_11_invalid_json_and_unknown_type(self):

        ws = await self.connect()

        # Invalid JSON
        await ws.send(
            "{this is not valid json"
        )

        invalid_json = await recv_until_type(
            ws,
            "error"
        )

        self.assertEqual(
            invalid_json["code"],
            "INVALID_JSON"
        )

        # Unknown request type
        await ws.send(json.dumps({

            "type": "does_not_exist"
        }))

        unknown = await recv_until_type(
            ws,
            "error"
        )

        self.assertEqual(
            unknown["code"],
            "UNKNOWN_MESSAGE_TYPE"
        )

        await ws.close()

    # -------------------------------------------------
    # TEST 12 - CONCURRENCY TEST
    # -------------------------------------------------

    async def test_12_concurrent_messages_have_unique_ids_and_no_loss(self):

        (
            alice,
            bob,
            _,
            _,
            conv_id

        ) = await self.make_two_users_and_conversation()

        async def send_many(
            ws,
            prefix,
            count
        ):

            for i in range(count):

                await ws.send(json.dumps({

                    "type": "send_message",

                    "conversation_id": conv_id,

                    "content": f"{prefix}-{i}"
                }))

        per_user = 15

        # Alice and Bob send simultaneously.
        await asyncio.gather(

            send_many(
                alice,
                "A",
                per_user
            ),

            send_many(
                bob,
                "B",
                per_user
            )
        )

        async def collect_new_messages(
            ws,
            count
        ):

            messages = []

            while len(messages) < count:

                msg = await recv_until_type(
                    ws,
                    "new_message",
                    timeout=4.0
                )

                messages.append(msg)

            return messages

        # Both users should receive all 30 messages.
        (
            alice_received,
            bob_received

        ) = await asyncio.gather(

            collect_new_messages(
                alice,
                per_user * 2
            ),

            collect_new_messages(
                bob,
                per_user * 2
            )
        )

        self.assertEqual(
            len(alice_received),
            per_user * 2
        )

        self.assertEqual(
            len(bob_received),
            per_user * 2
        )

        # Check stored messages.
        stored = server.load_messages()

        self.assertEqual(
            len(stored),
            per_user * 2
        )

        ids = [
            m["message_id"]
            for m in stored
        ]

        # Every message must have a unique ID.
        self.assertEqual(
            len(ids),
            len(set(ids)),
            "Message IDs must be unique"
        )

        contents = {
            m["content"]
            for m in stored
        }

        expected = {

            f"A-{i}"
            for i in range(per_user)

        } | {

            f"B-{i}"
            for i in range(per_user)
        }

        # Make sure no messages disappeared.
        self.assertEqual(
            contents,
            expected
        )

        await alice.close()
        await bob.close()


if __name__ == "__main__":

    unittest.main(
        verbosity=2
    )