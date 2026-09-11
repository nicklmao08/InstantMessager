let currentcontact=null;

let conversations={
    Mom:[{
        text:"message",
        type:"received"
    }
    ],
    Dad:[{
        text:"message",
        type:"received"
    }]
}

const username = sessionStorage.getItem("username");
const socket = new WebSocket("ws://10.176.31.71:8765");

socket.onopen = function() {
    socket.send(JSON.stringify({
        type: "login",
        username: username
    }));
};

socket.onmessage = function(event) {
    const data = JSON.parse(event.data);

    if (data.type === "message") {
        if (!conversations[data.from]) {
            conversations[data.from] = [];
        }

        conversations[data.from].push({
            text: data.content,
            type: "received"
        });

        if (currentContact === data.from) {
            displayMessages();
        }
    }
};

/*click contact  */
function openChat(contactName) {

    currentContact = contactName;

    document.getElementById("contactName").textContent =
        contactName;

    displayMessages();
}

/*send Message*/
function sendMessage() {
    const input =
        document.getElementById("messageInput");
    const message =
        input.value.trim();
    if (currentContact === null) {
        alert("Please select a contact first");
        return;
    }
    if (message === "") {
        return;
    }
    conversations[currentContact].push({
        text: message,
        type: "sent"
    });

    socket.send(JSON.stringify({
        type: "send_message",
        to: currentContact,
        content: message
    }));

    input.value = "";
    displayMessages();
}
document
    .getElementById("messageInput")
    .addEventListener("keydown", function(event) {
        if (event.key === "Enter") {
            sendMessage();
        }
    });

/*Display message */
function displayMessages() {
    const messagesDiv =
        document.getElementById("messages");
    messagesDiv.innerHTML = "";
    const messages =
        conversations[currentContact];
    messages.forEach(message => {
        const messageElement =
            document.createElement("div");
        messageElement.textContent =
            message.text;
        messageElement.classList.add(
            message.type
        );
        messagesDiv.appendChild(
            messageElement
        );
    });
}