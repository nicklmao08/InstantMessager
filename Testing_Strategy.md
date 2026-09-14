# InstantMessager 

## Testing Strategy

**Project:** InstantMessager  
**Testing scope:** WebSocket backend, client-server protocol, concurrency, persistence, and browser GUI 
**Deadline:** September 13, 2026

**Members:** 陈淳希 1820242104, 余善炜 1820242133, 陈瑞玲 1820242113, 谢粮璟 1820242151, 刘颖妮 1820242126

## 1. Purpose

The goal of testing is to verify that InstantMessager behaves correctly under normal use, invalid input, network failure, and concurrent activity. Testing is divided into **automated backend/integration tests** and **manual GUI tests**. This separation allows the networking and conversation logic to be tested independently of the browser interface, while visual behavior is checked manually.

## 2. What We Test Automatically

The automated suite is implemented in `test_server_automated.py` using Python's built-in `unittest` framework together with real local WebSocket connections. Each test starts an isolated server on a temporary port, resets the in-memory server state, and redirects message persistence to a temporary `messages.json` file. Therefore, running the tests does not modify the project's real message history.

### Automated test cases

| ID | Area | Test | Expected result |
|---|---|---|---|
| A01 | Connection | Connect to the WebSocket server | Server returns `connected` with protocol version `1.0` |
| A02 | Login | Login using a valid username | Login succeeds and user appears online |
| A03 | Validation | Login using an empty username | Server returns `INVALID_USERNAME` |
| A04 | Login/concurrency | Two clients use the same online username | Second login is rejected |
| A05 | Authorization | Request user data before login | Server returns `NOT_AUTHENTICATED` |
| A06 | Conversations | Create a conversation and request conversation list | Conversation is visible to participants |
| A07 | Messaging | Alice sends a message to Bob | Both participants receive the same `new_message` and it is persisted |
| A08 | Persistence | Request history after sending a message | Saved message is returned by `get_messages` |
| A09 | Validation | Send whitespace-only message | Server returns `INVALID_CONTENT` and saves nothing |
| A10 | Access control | Non-participant reads/sends to another conversation | Server returns `ACCESS_DENIED` |
| A11 | Protocol errors | Send invalid JSON / unknown type | Correct protocol errors are returned without crashing |
| A12 | Concurrency | Alice and Bob send messages concurrently | No message loss; all message IDs are unique |

### Why these tests are automated

These behaviors have clear expected outputs and can be checked using assertions. Automated tests are repeatable and make regression testing easier after changes to `server.py` or the client-server protocol.

## 3. Concurrency Testing

InstantMessager uses `asyncio` and WebSockets, so concurrency tests focus on simultaneous client activity rather than OS threads. The automated concurrency test connects two users to the same conversation and has both send a burst of messages at the same time with `asyncio.gather()`.

The test verifies that:

- every sent message is stored;
- every participant receives every message;
- message IDs remain unique;
- messages remain associated with the correct conversation;
- the server stays responsive while both users are active.

The current backend keeps user and conversation state inside one `asyncio` event loop. File persistence is synchronous, so `save_message()` does not yield control during its read-modify-write sequence. This avoids overlapping writes in the current single-process design, although it can temporarily block the event loop. If the application later introduces thread pools, multiple server processes, or a database, persistence should use a database transaction or an appropriate lock.

## 4. Manual GUI Testing

The front end is tested manually because layout, scrolling, visual feedback, and browser interaction are most easily evaluated by a person. At least two browser windows should be used for multi-user tests.

| ID | Manual test | Procedure | Expected result |
|---|---|---|---|
| M01 | Login validation | Leave username/password empty | Error is displayed and navigation is blocked |
| M02 | Password validation | Enter password shorter than 8 characters | Password warning is displayed |
| M03 | Successful navigation | Enter valid login fields | User is taken to the chat page |
| M04 | Contact selection | Select a contact | Correct contact name and conversation appear |
| M05 | Send button | Type a message and click Send | Message appears once in the correct conversation |
| M06 | Enter key | Type a message and press Enter | Same behavior as Send button |
| M07 | Empty message | Press Send with empty/whitespace text | No message is sent |
| M08 | Unicode | Send Chinese text and emoji | Text is preserved and displayed correctly |
| M09 | Long text | Send a long message | Text wraps without breaking the layout |
| M10 | Real-time delivery | Open Alice and Bob in separate windows and send messages | Receiver sees messages without refreshing |
| M11 | Scrolling | Send enough messages to exceed the message area | Scrolling works and recent messages remain reachable |
| M12 | Resize | Resize browser window | Main chat controls remain usable and readable |
| M13 | Disconnect | Close one user's tab while another stays connected | Remaining client/server stay operational |
| M14 | Reconnect | Reopen and log in again | User can connect again and retrieve messages |

For every manual test, record the browser, steps, expected result, actual result, pass/fail status, and a screenshot when a defect is found.

## 5. Client-Server Integration Tests

The browser front end and backend must also be tested together. This is especially important because both sides must implement exactly the same JSON protocol.

The current server expects message sending in this form:

```json
{
  "type": "send_message",
  "conversation_id": 1,
  "content": "Hello"
}
```

and delivers messages as `new_message`.

During manual integration testing, verify that the browser sends this exact structure and handles server responses such as `login_response`, `user_list`, `conversation_list`, `message_history`, `new_message`, and `error`.

## 6. Network and Failure Testing

The following failure cases are tested manually:

1. Start the browser while the WebSocket server is stopped. The page should report or handle the connection failure rather than freeze.
2. Stop the server while two users are connected. Clients should not become unusable because of an unhandled exception.
3. Close one browser suddenly. The server should mark that user offline and continue serving other users.
4. Restart the server and reconnect clients. New connections should work normally.
5. Send malformed requests using an automated WebSocket test client. The server should return an `error` message and remain running.

## 7. Regression Testing

The automated test suite should be run before merging backend or protocol changes into `main`.

Run:

```bash
python3 -m unittest -v test_server_automated.py
```

A change should not be merged if an existing test fails unless the protocol/design has intentionally changed and the corresponding tests and documentation are updated.

The GUI checklist should also be repeated after changes to `Index.html`, `Chatlog.html`, `Main.js`, `chat.js`, or `style.css`.

## 8. Pass Criteria

The backend is considered ready for the project demonstration when:

- all automated tests pass;
- two or more clients can communicate in real time;
- invalid requests do not crash the server;
- unauthorized conversation access is rejected;
- concurrent test messages are not lost or duplicated;
- manual GUI tests for login, contact selection, messaging, scrolling, and reconnection pass;
- known defects are documented before submission.

## 9. Test Result Record

Use the following format when recording manual tests:

| Test ID | Date | Tester | Expected | Actual | Result | Evidence/Notes |
|---|---|---|---|---|---|---|
| M01 | | | Error shown | | Pass/Fail | |

This gives a clear record showing that the testing strategy was actually performed rather than only described.
