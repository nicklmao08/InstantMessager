# InstantMessager

## Conversation Design

**Project:** InstantMessager  
**Deadline:** September 6, 2026

---

# 1. Conversation Definition

A conversation is an interactive text-exchange session between two or more users.

Each conversation has a unique `conversation_id` and contains the messages exchanged between its participants.

Example:

```text
Conversation 10

Participants:
- Alice
- Bob

Alice: Hello Bob!
Bob: Hi Alice!
```

A conversation may also contain multiple participants:

```text
Conversation 20

Participants:
- Alice
- Bob
- Charlie
```

# 2. Users and Participants

Each user has:

- `user_id` — unique identifier
- `username` — unique username
- `online` — current connection status

Example:

```json
{
  "user_id": 1,
  "username": "Alice",
  "online": true
}
```

A conversation contains a list of participants. Only participants of a conversation can access its messages or send messages to that conversation.

When creating a conversation, the client specifies participants using their user IDs through the participant_ids field. Existing conversations represent these users as participants.

# 3. Conversation Structure

A conversation consists of:

```text
Conversation
│
├── conversation_id
├── participants
│
└── messages
    ├── message_id
    ├── sender_id
    ├── sender_username
    ├── content
    └── timestamp
```

Example:

```json
{
  "conversation_id": 10,
  "participants": [1, 2],
  "messages": [
    {
      "message_id": 57,
      "sender_id": 1,
      "sender_username": "Alice",
      "content": "Hello Bob!",
      "timestamp": "2026-09-01T15:30:00"
    }
  ]
}
```

# 4. Messages

Every message belongs to exactly one conversation.

A message contains:

- `message_id`
- `conversation_id`
- `sender_id`
- `sender_username`
- `content`
- `timestamp`

The server generates the message ID and timestamp.

Messages are displayed in chronological order.

# 5. Instant Messaging

When a user sends a message, the server immediately delivers it to the connected participants of the conversation.

Example:

```text
Alice
  |
  | "Hello Bob!"
  v
Server
  |
  v
Bob
```

If a participant is offline, the message remains in the conversation history and can be retrieved when the user reconnects.

# 6. Conversation Separation

Messages belonging to different conversations must remain separate.

For example:

```text
Conversation: Alice + Bob

Alice: Hello!
Bob: Hi!
```

```text
Conversation: Alice + Charlie

Alice: Are you free?
Charlie: Yes!
```

A message from one conversation must not appear in another conversation.

# 7. Conversation Lifecycle

A conversation follows this general lifecycle:

```text
Create Conversation
        |
        v
Add Participants
        |
        v
Exchange Messages
        |
        v
Store Message History
        |
        v
Retrieve History Later
```

The conversation continues to exist even when all participants are temporarily offline.

# 8. Design Principles

The conversation design follows these principles:

1. Every conversation has a unique ID.
2. A conversation contains two or more participants.
3. Every message belongs to one conversation.
4. Only participants can access the conversation.
5. Messages are stored as conversation history.
6. Connected users receive messages immediately.
7. Offline users can retrieve previous messages later.
8. Messages from different conversations remain separated.

# 9. Relationship to Client-Server Protocol

The conversation design defines the concepts and behavior of the messaging system. These concepts are implemented through the client-server protocol.

For example:

- Users are managed through `login`, `get_users`, and `user_status`.
- Conversations are managed through `get_conversations` and `create_conversation`.
- Messages are retrieved through `get_messages`.
- New messages are sent using `send_message` and delivered using `new_message`.

For the detailed message formats and communication flow, see [Client-Server Protocol](Client_Server_Protocol.md).