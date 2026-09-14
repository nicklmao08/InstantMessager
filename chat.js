const currentUsername = sessionStorage.getItem("username");
let currentContact = null;
let users = [];
let contacts =[];
let conversations = {};

/* Up users */
function updateUsers(newUsers) {

    users = newUsers.filter(function(user) {
        return user.username !== currentUsername;
    });
}
function addContact() {

    const input =
        document.getElementById("contactUsername");

    const username =
        input.value.trim();

    const error =
        document.getElementById("contactError");


    // Empty input
    if (username === "") {
        error.textContent = "Enter a username";
        return;
    }


    // Cannot add yourself
    if (username === currentUsername) {
        error.textContent = "You cannot add yourself";
        return;
    }


    // Find user from users list
    const foundUser =
        users.find(function(user) {
            return user.username === username;
        });


    // Username doesn't exist
    if (!foundUser) {
        error.textContent = "User not found";
        return;
    }


    // Check if already added
    const alreadyAdded =
        contacts.some(function(contact) {
            return contact.username === username;
        });


    if (alreadyAdded) {
        error.textContent = "User already added";
        return;
    }


    // Add contact
    contacts.push(foundUser);

    error.textContent = "";

    input.value = "";

    renderContacts();
}

/* Display users */
function renderContacts() {

    const contactsDiv =
        document.getElementById("contacts");

    contactsDiv.innerHTML = "";


    contacts.forEach(function(contact) {

        const contactDiv =
            document.createElement("div");

        contactDiv.classList.add("contact");


        contactDiv.addEventListener(
            "click",
            function() {
                openUserChat(contact.username);
            }
        );


        const icon =
            document.createElement("img");

        icon.src = "Images/user.png";

        icon.classList.add("contactIcon");


        const name =
            document.createElement("span");

        name.textContent =
            contact.username;


        const status =
            document.createElement("span");

        status.classList.add("status-dot");


        if (contact.status === "online") {

            status.classList.add(
                "status-online"
            );

        }
        else {

            status.classList.add(
                "status-offline"
            );

        }


        contactDiv.appendChild(icon);

        contactDiv.appendChild(name);

        contactDiv.appendChild(status);

        contactsDiv.appendChild(contactDiv);
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

