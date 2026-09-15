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

function openChat(conversationId) {

    currentContact =
        conversationId;

    const conversation =
        conversations[conversationId];


    document.getElementById("contactName").textContent =
        conversation.name || conversationId;


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
            icon.textContent="👥";
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

function showGroupForm() {

    const form =
        document.getElementById("groupForm");

    form.style.display = "block";

    renderGroupContacts();
}

function renderGroupContacts() {

    const container =
        document.getElementById("groupContacts");

    container.innerHTML = "";


    contacts.forEach(function(contact) {

        const row =
            document.createElement("div");


        const checkbox =
            document.createElement("input");

        checkbox.type = "checkbox";
        checkbox.value = contact.username;
        checkbox.classList.add("group-member");


        const label =
            document.createElement("span");

        label.textContent =
            contact.username;


        row.appendChild(checkbox);
        row.appendChild(label);

        container.appendChild(row);
    });
}
function renderGroupContacts() {

    const container =
        document.getElementById("groupContacts");

    container.innerHTML = "";


    contacts.forEach(function(contact) {

        const row =
            document.createElement("div");


        const checkbox =
            document.createElement("input");

        checkbox.type = "checkbox";
        checkbox.value = contact.username;
        checkbox.classList.add("group-member");


        const label =
            document.createElement("span");

        label.textContent =
            contact.username;


        row.appendChild(checkbox);
        row.appendChild(label);

        container.appendChild(row);
    });
}
function createGroup() {

    const groupName =
        document.getElementById("groupName").value.trim();

    const error =
        document.getElementById("groupError");


    if (groupName === "") {
        error.textContent =
            "Enter a group name";
        return;
    }


    const selected =
        document.querySelectorAll(
            ".group-member:checked"
        );


    const selectedMembers = [];

    selected.forEach(function(checkbox) {
        selectedMembers.push(checkbox.value);
    });


    if (selectedMembers.length < 2) {

        error.textContent =
            "Select at least 2 contacts";

        return;
    }


    const conversationId =
        "group_" + groupName;


    if (conversations[conversationId]) {

        error.textContent =
            "Group already exists";

        return;
    }


    conversations[conversationId] = {

        name: groupName,

        type: "group",

        members: [
            currentUsername,
            ...selectedMembers
        ],

        messages: []
    };


    error.textContent = "";

    document.getElementById("groupName").value = "";

    document.getElementById("groupForm").style.display =
        "none";


    renderConversations();

    openChat(conversationId);
}
function renderConversations() {

    const conversationDiv =
        document.getElementById("conversationList");

    conversationDiv.innerHTML = "";


    Object.keys(conversations).forEach(function(id) {

        const conversation =
            conversations[id];


        const conversationRow =
            document.createElement("div");

        conversationRow.classList.add("contact");


        conversationRow.addEventListener(
            "click",
            function() {
                openChat(id);
            }
        );


        const icon =
            document.createElement("span");

        if (conversation.type === "group") {
            icon.textContent = "👥";
        }
        else {
            icon.textContent = "💬";
        }


        const name =
            document.createElement("span");

        name.textContent =
            conversation.name || id;


        conversationRow.appendChild(icon);
        conversationRow.appendChild(name);

        conversationDiv.appendChild(
            conversationRow
        );
    });
}
function openUserChat(username) {

    if (!conversations[username]) {

        conversations[username] = {

            name: username,

            type: "private",

            members: [
                currentUsername,
                username
            ],

            messages: []
        };

        renderConversations();
    }

    openChat(username);
}

updateUsers([
    {
        username: "Alice",
        status: "online"
    },
    {
        username: "Nick",
        status: "online"
    },
    {
        username: "Mom",
        status: "offline"
    },
    {
        username: "Dad",
        status: "online"
    }
]);
