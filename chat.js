const currentUsername = sessionStorage.getItem("username");
let currentContact = null;
let users = [];

let conversations = {
    Mom: {
        members: [currentUsername, "Mom"],
        messages: [
            {
                sender: "Mom",
                text: "message",
                type: "received"
            }
        ]
    },

    Dad: {
        members: [currentUsername, "Dad"],
        messages: [
            {
                sender: "Dad",
                text: "udh kirim uang",
                type: "received"
            }
        ]
    }
};

/* Up users */
function updateUsers(newUsers) {

    users = newUsers.filter(function(user) {
        return user.username !== currentUsername;
    });

    renderUsers();
}

/* Display users */
function renderUsers() {

    const usersDiv =
        document.getElementById("onlineUsers");
    usersDiv.innerHTML = "";
    users.forEach(function(user) {
        const userDiv =
            document.createElement("div");
        userDiv.classList.add("contact");

        userDiv.addEventListener("click", function() {
            openUserChat(user.username);
        });
        const userIcon =
            document.createElement("img");
        userIcon.src = "Images/user.png";
        userIcon.classList.add("contactIcon");

        const username =
            document.createElement("span");
        username.textContent = user.username;
        // Status
        const status =
            document.createElement("span");
        status.classList.add("status-dot");
        if (user.status === "online") {
            status.classList.add("status-online");
        }
        else {
            status.classList.add("status-offline");
        }
        userDiv.appendChild(userIcon);
        userDiv.appendChild(username);
        userDiv.appendChild(status);
        usersDiv.appendChild(userDiv);
    });
}

function openUserChat(username) {
    if (!conversations[username]) {
        conversations[username] = {
            members: [currentUsername, username],
            messages: []
        };
    }
    openChat(username);
}

function openChat(contactName) {
    currentContact = contactName;
    document.getElementById("contactName").textContent =
        contactName;
    displayMessages();
}


/* Send mesg */
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
    conversations[currentContact].messages.push({
        sender: currentUsername,
        text: message,
        type: "sent"
    });
    input.value = "";
    displayMessages();
}


/* Press Enter */
document
    .getElementById("messageInput")
    .addEventListener("keydown", function(event) {
        if (event.key === "Enter") {
            sendMessage();
        }
    });


/* Disp mesg */
function displayMessages() {
    const messagesDiv =
        document.getElementById("messages");
    messagesDiv.innerHTML = "";
    if (currentContact === null) {
        return;
    }
    const messages =
        conversations[currentContact].messages;
    messages.forEach(function(message) {
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


/* Rec msg */
function receiveMessage(conversationName, sender, text) {
    if (!conversations[conversationName]) {

        conversations[conversationName] = {
            members: [currentUsername, sender],
            messages: []
        };
    }
    conversations[conversationName].messages.push({
        sender: sender,
        text: text,
        type: "received"
    });
    if (currentContact === conversationName) {
        displayMessages();
    }
}


/*  testing */
updateUsers([
    {
        username: currentUsername,
        status: "online"
    },

    {
        username: "Mom",
        status: "online"
    },

    {
        username: "Dad",
        status: "offline"
    },

    {
        username: "Bob",
        status: "online"
    },

    {
        username: "Nick",
        status: "offline"
    }
]);