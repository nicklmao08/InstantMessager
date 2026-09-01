# InstantMessager
whatsgood gang gang

# Github
to get started jus google "how to start working on a git repository in vscode"
if this file gets on your PC then it has worked

after that, every time you wanna work, use this command in the terminal:
1. "git pull" to get the newest version from github. PLS dont forget to do this BEFORE working. Just in case.

then to save changes, u need all three down here
2. "git add ."
3. "git commit {message}" put in whatever the change was
4. "git push"

# JSON Formatting
| Message                      | Direction | JSON inside data                                                                                                                 |
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
 