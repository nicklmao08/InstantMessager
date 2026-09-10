## Concurrency Strategy

**Project:** InstantMessager  
**Deadline:** September 13, 2026

# 1. Concurrency Approach

InstantMessager uses Python `asyncio` together with WebSockets to handle multiple users concurrently.

The server runs an asynchronous event loop. Each connected client is handled by an asynchronous `handle_client()` function, allowing the server to communicate with multiple clients without creating a separate thread for every user.

```text
             WebSocket Server
                   |
    +--------------+--------------+
    |              |              |
  Alice           Bob          Charlie
 client          client          client
    |              |              |
 async           async           async
connection       connection      connection
```

This allows users to remain connected and send or receive messages at the same time.

# 2. Concurrent Client Handling

Each WebSocket connection is handled asynchronously.

When a client connects:

1. The server creates a connection for the client.
2. The client can log in.
3. The server stores the user's connection information.
4. The server continues handling other connected clients concurrently.
5. Incoming messages are processed according to their message type.

The server does not need to wait for one client to finish before handling another client.

# 3. Shared Server State

The server maintains shared state for:

- Registered users
- Currently connected users
- Conversations
- Conversation participants
- Message history
- User, conversation, and message IDs

```text
Server State
├── registered_users
├── users
├── conversations
└── messages.json
```

This shared state allows different clients to interact with the same conversations and users.

# 4. Concurrent Message Delivery

When a user sends a message, the server:

1. Checks that the user is logged in.
2. Checks that the conversation exists.
3. Checks that the user is a participant.
4. Saves the message to the message history.
5. Sends the new message to connected participants.

```text
Alice
  |
  | send_message
  v
Server
  |
  +------> Bob
  |
  +------> Charlie
```

Only participants of the conversation receive the message. If a participant is offline, the message remains in the conversation history and can be retrieved later.

# 5. Connection and Disconnection

When a user logs in:

```text
User connects
      ↓
Login
      ↓
User marked online
      ↓
User list/status updated
```

When a user disconnects:

```text
User disconnects
      ↓
Connection removed
      ↓
User marked offline
      ↓
User status updated
```

This allows other clients to receive the user's current online status.

# 6. Consistency of Shared Data

The current implementation uses a single Python `asyncio` event loop for client handling and keeps server state in shared in-memory structures.

Message history is stored in `messages.json`. Messages are loaded, updated, and saved by the server when a new message is created.

For the current project scope, this provides a simple way to maintain consistent conversation history while multiple clients are connected.

A future improvement would be to use an `asyncio.Lock` or a database for message persistence if the system needs to support a larger number of simultaneous users and concurrent writes.

# 7. Concurrency Goals

The concurrency strategy aims to ensure that:

1. Multiple clients can remain connected at the same time.
2. One client's activity does not block other clients unnecessarily.
3. Messages are delivered to the correct conversation participants.
4. User online/offline status is updated when connections change.
5. Message history remains associated with the correct conversation.
6. Shared server state remains consistent.

# 8. Summary

InstantMessager uses asynchronous WebSocket communication with Python `asyncio` as its main concurrency strategy.

Each client connection is handled asynchronously, while the server maintains shared user, conversation, and message state. This approach is suitable for the project's real-time messaging requirements and allows multiple users to communicate concurrently.