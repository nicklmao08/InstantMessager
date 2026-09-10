# InstantMessager

# Documentation
The project documentation is divided into two main parts:

- [Conversation Design](Conversation_Design.md) — defines the structure and behavior of users, conversations, participants, and messages.
- [Client-Server Protocol](Client_Server_Protocol.md) — defines how the client and server communicate using WebSockets and JSON.

The Conversation Design describes what the system should do, while the Client-Server Protocol describes how the client and server implement that design.

# GitHub
to get started just google "how to start working on a git repository in vscode"
if this file gets on your PC then it has worked

after that, every time you wanna work, use this command in the terminal:
1. "git pull" to get the newest version from github. Please dont forget to do this BEFORE working. Just in case.

To save changes:
1. `git status` — check which files changed.
2. `git add <file>` — add only the files you want to commit.
3. `git commit -m "Describe your changes"`
4. `git push`

# Protocol Summary
The following table provides a quick overview of the client-server message types. For the complete protocol specification and examples, see [Client-Server Protocol](Client_Server_Protocol.md).

| Message | Direction | Example Payload |
| ---------------------------- | --------- | -------------------------------------------------------------------------------------------------------------------------------- |
| connected                    | S → C     | { "protocol_version": "1.0" }                                                                                                    |
| login                        | C → S     | { "username": "Alice" }                                                                                                          |
| login_response               | S → C     | { "success": true, "user": {...} }                                                                                               |
| get_users                    | C → S     | {}                                                                                                                               |
| user_list                    | S → C     | { "users": [...] }                                                                                                               |
| user_status                  | S → C     | { "user_id": 2, "username": "Bob", "online": true }                                                                              |
| get_conversations            | C → S     | {}                                                                                                                               |
| conversation_list            | S → C     | { "conversations": [...] }                                                                                                       |
| create_conversation          | C → S     | { "name": "...", "participant_ids": [...] }                                                                                      |
| create_conversation_response | S → C     | { "success": true, "conversation": {...} }                                                                                       |
| get_messages                 | C → S     | { "conversation_id": 10 }                                                                                                        |
| message_history              | S → C     | { "conversation_id": 10, "messages": [...] }                                                                                     |
| send_message                 | C → S     | { "conversation_id": 10, "content": "Hello!" }                                                                                   |
| new_message                  | S → C     | { "message_id": 57, "conversation_id": 10, "sender_id": 1, "sender_username": "Alice", "content": "Hello!", "timestamp": "..." } |
| error                        | S → C     | { "code": "...", "message": "..." }                                                                                              |
 