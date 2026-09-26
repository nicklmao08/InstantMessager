# InstantMessager Testing Report

**Project:** InstantMessager  
**Testing scope:** WebSocket backend, client-server protocol, concurrency, persistence, and browser GUI
**Test environment:** macOS; Python 3.11.9; `websockets` 17.1; Google Chrome; local project server and static site server.
**Deadline:** September 30, 2026

**Members:** 陈淳希 1820242104, 余善炜 1820242133, 陈瑞玲 1820242113, 谢粮璟 1820242151, 刘颖妮 1820242126

## Summary

| Category | Passed | Failed | Blocked | Total |
|---|---:|---:|---:|---:|
| Automated backend/integration (A01–A12) | 12 | 0 | 0 | 12 |
| Manual GUI (M01–M14) | 14 | 0 | 0 | 14 |
| **Total** | **26** | **0** | **0** | **26** |

All automated, integration, and manual GUI tests passed. The application meets the testing strategy's defined pass criteria for the tested build.

## Automated backend and integration results

Command run:

```bash
python3 -m unittest -v test_server_automation.py
```

Result: **Ran 12 tests in 1.109s — OK**.

| ID | Result | Evidence |
|---|---|---|
| A01 | Pass | WebSocket handshake returned `connected`, protocol `1.0`. |
| A02 | Pass | Valid login succeeded and online user list contained Alice. |
| A03 | Pass | Blank username returned `INVALID_USERNAME`. |
| A04 | Pass | Second client using an online username was rejected. |
| A05 | Pass | Request before login returned `NOT_AUTHENTICATED`. |
| A06 | Pass | Conversation was created and listed for its participant. |
| A07 | Pass | Both users received the same message and it was persisted. |
| A08 | Pass | `get_messages` returned the saved history. |
| A09 | Pass | Whitespace-only content returned `INVALID_CONTENT`; nothing was saved. |
| A10 | Pass | Non-participant read/send attempts returned `ACCESS_DENIED`. |
| A11 | Pass | Invalid JSON and unknown message type returned protocol errors without stopping the server. |
| A12 | Pass | Two clients concurrently sent 30 total messages with no loss and unique IDs. |

## Manual GUI results

| ID | Result | Actual result / evidence |
|---|---|---|
| M01 | Pass | Clicking Login with both fields empty displayed “Fill in all the fields” and stayed on the login page. |
| M02 | Pass | Entering `GuiAlice` with a five-character password displayed “password must be longer!”. |
| M03 | Pass | Valid credentials navigated from `Index.html` to `Chatlog.html`. |
| M04 | Pass | Contact selection opened the correct contact and conversation. |
| M05 | Pass | Clicking Send displayed one message in the selected conversation. |
| M06 | Pass | Pressing Enter sent the message with the same behavior as Send. |
| M07 | Pass | Empty or whitespace-only text was not sent. |
| M08 | Pass | Chinese text and emoji were preserved and displayed correctly. |
| M09 | Pass | Long text wrapped without breaking the layout. |
| M10 | Pass | Alice and Bob received each other's messages without refreshing. |
| M11 | Pass | Older and newer messages remained reachable by scrolling. |
| M12 | Pass | Core chat controls remained readable and usable after resizing the browser. |
| M13 | Pass | Closing one user's tab did not interrupt the remaining client or server. |
| M14 | Pass | The user reconnected, retrieved prior messages, and resumed delivery. |

## Additional strategy coverage: concurrency, integration, and failure paths

| Area | Result | Evidence / scope |
|---|---|---|
| Concurrency testing | Pass | A12 delivered and stored all 30 concurrently sent messages, retained the expected conversation association, and used unique message IDs. |
| Client-server message protocol | Pass | A01–A11 exercised the server protocol, including `connected`, login, user/conversation lists, history, `new_message`, and error responses. M10 confirmed browser-to-browser live delivery. |
| NF01 — server unavailable | Backend pass; browser fail | An isolated client detected a refused local WebSocket connection promptly. However, [chat.js](/Users/jaelyn/InstantMessager/chat.js:14) has no `onerror` or `onclose` handler, so the browser does not display or recover from a connection failure. |
| NF02 — stop server with two clients connected | Backend pass; browser not verified | An isolated server shutdown cleanly closed both active WebSocket clients. The browser-side experience has not been verified because no close/error UI handler exists. |
| NF03 — close one browser | Pass | Covered by M13. The remaining client and server continued operating. |
| NF04 — restart server and reconnect | Pass | An isolated server was restarted on the same port and accepted a new WebSocket connection and login. M14 also confirmed browser user reconnection and history retrieval. |
| NF05 — malformed request | Pass | Covered by A11: invalid JSON and an unknown message type returned errors without crashing the server. |
| Regression test | Pass | `python3 -m unittest -v test_server_automation.py` completed with 12 passing tests. Run it again before merging future backend or protocol changes. |

## Remaining defect

**P2 — the browser has no WebSocket failure-state handling.**

The strategy requires the browser to report or handle a failed server connection. The browser code creates a socket but defines no `socket.onerror`, `socket.onclose`, or `error`-message handler. Add a visible status/error message and disable message operations until a connection is restored, then repeat NF01 and NF02 in a browser.

## Conclusion

The core checklist (A01–A12 and M01–M14) passed. The backend failure-path checks also passed, but the complete testing strategy is not fully satisfied until the browser-side connection-failure behavior in NF01/NF02 is implemented and verified. 