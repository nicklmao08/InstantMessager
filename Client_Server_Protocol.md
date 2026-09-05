# InstantMessager

## Client-Server Protocol

**Project:** InstantMessager  
**Deadline:** September 6, 2026

**Members:** 陈淳希 1820242104, 余善炜 1820242133, 陈瑞玲 1820242113, 谢粮璟 1820242151, 刘颖妮 1820242126

This protocol implements the concepts defined in the [Conversation Design](Conversation_Design.md).

The Conversation Design describes the structure and behavior of the messaging system, while this document defines the messages exchanged between the client and server to implement that design.

---

# 1. Communication Method

The client and server communicate using WebSockets.

During development, the server runs at:

```text
ws://localhost:8765
```

Messages exchanged between the client and server use JSON.

Every protocol message contains a `type` field.

General format:

```json
{
  "type": "<message_type>"
}
```

# 2. Protocol Messages

| Message Type | Direction | Purpose |
|---|---|---|
| `connected` | S → C | Indicates that the WebSocket connection has been established. |
| `login` | C → S | Allows a client to log in. |
| `login_response` | S → C | Returns the result of a login request. |
| `get_users` | C → S | Requests the list of users. |
| `user_list` | S → C | Returns the list of users. |
| `user_status` | S → C | Notifies clients when a user's online status changes. |
| `get_conversations` | C → S | Requests the conversations available to the user. |
| `conversation_list` | S → C | Returns the user's conversations. |
| `create_conversation` | C → S | Creates a new conversation. |
| `create_conversation_response` | S → C | Returns the result of conversation creation. |
| `get_messages` | C → S | Requests message history for a conversation. |
| `message_history` | S → C | Returns messages belonging to a conversation. |
| `send_message` | C → S | Sends a new message to a conversation. |
| `new_message` | S → C | Delivers a newly sent message to participants. |
| `error` | S → C | Reports an error to the client. |

# 3. Connection

When a client connects to the server, the server sends:

```json
{
  "type": "connected",
  "protocol_version": "1.0"
}
```

# 4. Login

The client sends:

```json
{
  "type": "login",
  "username": "Alice"
}
```

The server responds with:

```json
{
  "type": "login_response",
  "success": true,
  "user": {
    "user_id": 1,
    "username": "Alice",
    "online": true
  }
}
```

If login fails:

```json
{
  "type": "login_response",
  "success": false,
  "message": "Username already exists."
}
```

# 5. Get Users

The client requests the current users:

```json
{
  "type": "get_users"
}
```

The server responds:

```json
{
  "type": "user_list",
  "users": [
    {
      "user_id": 1,
      "username": "Alice",
      "online": true
    },
    {
      "user_id": 2,
      "username": "Bob",
      "online": false
    }
  ]
}
```

# 6. User Status

When a user's connection status changes, the server sends:

```json
{
  "type": "user_status",
  "user_id": 2,
  "username": "Bob",
  "online": true
}
```

# 7. Get Conversations

The client requests its conversations:

```json
{
  "type": "get_conversations"
}
```

The server responds:

```json
{
  "type": "conversation_list",
  "conversations": [
    {
      "conversation_id": 10,
      "participants": [1, 2]
    }
  ]
}
```

# 8. Create Conversation

The client requests a new conversation:

```json
{
  "type": "create_conversation",
  "name": "Alice and Bob",
  "participants_ids": [1, 2]
}
```

The server responds:

```json
{
  "type": "create_conversation_response",
  "success": true,
  "conversation": {
    "conversation_id": 10,
    "name": "Alice and Bob",
    "participants": [1, 2]
  }
}
```

# 9. Get Message History

The client requests the messages of a conversation:

```json
{
  "type": "get_messages",
  "conversation_id": 10
}
```

The server responds:

```json
{
  "type": "message_history",
  "conversation_id": 10,
  "messages": [
    {
      "message_id": 57,
      "conversation_id": 10,
      "sender_id": 1,
      "sender_username": "Alice",
      "content": "Hello Bob!",
      "timestamp": "2026-09-01T15:30:00"
    }
  ]
}
```

# 10. Send Message

The client sends:

```json
{
  "type": "send_message",
  "conversation_id": 10,
  "content": "Hello Bob!"
}
```

The server creates the message ID and timestamp.

The server then sends the message to connected participants:

```json
{
  "type": "new_message",
  "message_id": 57,
  "conversation_id": 10,
  "sender_id": 1,
  "sender_username": "Alice",
  "content": "Hello Bob!",
  "timestamp": "2026-09-01T15:30:00"
}
```

# 11. Error Handling

When an invalid request is received, the server sends:

```json
{
  "type": "error",
  "code": "INVALID_REQUEST",
  "message": "Invalid request."
}
```

Examples of errors include:

- Invalid JSON
- Missing required fields
- User not logged in
- Conversation does not exist
- User is not a participant
- Invalid message content

# 12. Example Communication Flow

A basic conversation can follow this sequence:

```text
Client                         Server
  |                              |
  |-------- WebSocket ---------->|
  |                              |
  |<------- connected -----------|
  |                              |
  |---------- login ------------>|
  |                              |
  |<------ login_response -------|
  |                              |
  |---- get_conversations ------>|
  |                              |
  |<----- conversation_list -----|
  |                              |
  |------ get_messages --------->|
  |                              |
  |<------ message_history ------|
  |                              |
  |------ send_message --------->|
  |                              |
  |<-------- new_message --------|
  |                              |
```

# 13. Client State

The client may maintain:

- Connection status
- Logged-in user
- Online users
- Available conversations
- Current conversation
- Messages for the current conversation

# 14. Server State

The server maintains:

- Connected users
- User information
- Conversations
- Conversation participants
- Message history
- Message IDs
