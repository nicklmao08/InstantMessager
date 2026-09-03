
let currentcontact=null;

let conversations={
    Mom:[{
        text:"lu udh makan?",
        type:"received"
    }
    ],
    Dad:[{
        text:"udh kirim uang ya",
        type:"received"
    }]
}
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
