const currentUsername = sessionStorage.getItem("username");
let currentUserId = null;
let currentContact = null;
let users = [];

let contacts =
    JSON.parse(
        localStorage.getItem(
            "contacts_" + currentUsername
        )
    ) || [];

let conversations = {};
const socket = new WebSocket("ws://localhost:8765");

socket.onopen = function () {

    socket.send(JSON.stringify({
        type: "login",
        username: currentUsername
    }));

    socket.send(JSON.stringify({
        type: "get_conversations"
    }));

};

socket.onmessage = function(event) {

    const data = JSON.parse(event.data);

    console.log("Received:", data);

    if (data.type === "user_list") {
        updateUsers(data.users);
        renderContacts();
    }

    if (data.type === "login_response") {

        currentUserId =
            data.user.user_id;

        socket.send(JSON.stringify({
            type: "get_users"
        }));

    }

    if (data.type === "create_conversation_response") {

        const conversation = data.conversation;

        console.log(
            "Backend returned:",
            conversation
        );

        conversations[conversation.conversation_id] = {
            ...conversation,
            messages: []
        };

        renderConversations();

        openChat(conversation.conversation_id);
    }

    if (data.type === "message_history") {

        const conversation =
            conversations[data.conversation_id];

        conversation.messages = [];

        data.messages.forEach(function(message) {

            conversation.messages.push({

                sender: message.sender_username,

                text: message.content,

                type:
                    message.sender_username === currentUsername
                    ? "sent"
                    : "received"
            });

        });

        displayMessages();
    }

    if (data.type === "new_message") {

        const conversationId =
            data.conversation_id;

        if (!conversations[conversationId]) {
            return;
        }

        conversations[conversationId].messages.push({

            sender: data.sender_username,

            text: data.content,

            type:
                data.sender_username === currentUsername
                ? "sent"
                : "received"
        });

        if (currentContact === conversationId) {
            displayMessages();
        }
    }

    if (data.type === "conversation_list") {

        data.conversations.forEach(function(conversation) {

            conversations[
                conversation.conversation_id
            ] = {

                ...conversation,

                messages: []

            };

        });

        renderConversations();
    }

};

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
        console.log(contacts);
        contacts.some(function(contact) {
            return contact.username === username;
        });


    if (alreadyAdded) {
        error.textContent = "User already added";
        return;
    }


    // Add contact
    contacts.push(foundUser);
    localStorage.setItem(
        "contacts_" + currentUsername,
        JSON.stringify(contacts)
    );
    console.log("CONTACT ADDED:", foundUser.username);

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


        if (contact.online){

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

function openChat(conversationId) {

    console.log(
        "openChat called with:",
        conversationId,
        typeof conversationId
    );

    socket.send(JSON.stringify({
        type: "get_messages",
        conversation_id: conversationId
    }));

    currentContact =
        conversationId;

    const conversation =
        conversations[conversationId];


    let displayName =
        conversation.name || conversationId;

    if (
        conversation.participants &&
        conversation.participants.length === 2
    ) {

        const otherUserId =
            conversation.participants.find(
                participantId =>
                    participantId !== currentUserId
            );

        const otherUser =
            users.find(
                user =>
                    user.user_id === otherUserId
            );

        if (otherUser) {
            displayName =
                otherUser.username;
        }
    }

    document.getElementById("contactName").textContent =
        displayName;


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
    socket.send(JSON.stringify({

        type: "send_message",

        conversation_id: currentContact,

        content: message

    }));

    input.value = "";
    displayMessages();
}
document
    .getElementById("messageInput")
    .addEventListener("keydown", function(event) {

        if (event.key === "Enter") {
            event.preventDefault();
            sendMessage();
        }

    });

/*Display message */
function displayMessages() {

    const messagesDiv =
        document.getElementById("messages");

    messagesDiv.innerHTML = "";

    if (!currentContact || !conversations[currentContact]) {
        return;
    }

    const messages =
        conversations[currentContact].messages || [];

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

function createGroup() {

    const groupName =
        document.getElementById("groupName")
            .value
            .trim();

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

    const participantIds = [];

    selected.forEach(function(checkbox) {

        const contact =
            contacts.find(
                c =>
                    c.username === checkbox.value
            );

        if (contact) {
            participantIds.push(
                contact.user_id
            );
        }

    });

    if (participantIds.length < 2) {

        error.textContent =
            "Select at least 2 contacts";

        return;
    }

    console.log(
        "Creating group:",
        groupName,
        participantIds
    );

    socket.send(JSON.stringify({

        type: "create_conversation",

        name: groupName,

        participant_ids: participantIds

    }));

    error.textContent = "";

    document.getElementById("groupName").value =
        "";

    document.getElementById("groupForm").style.display =
        "none";
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
                openChat(Number(id));
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

        let displayName =
            conversation.name || id;

        if (
            conversation.participants &&
            conversation.participants.length === 2
        ) {

            const otherUserId =
                conversation.participants.find(
                    participantId =>
                        participantId !== currentUserId
                );

            const otherUser =
                users.find(
                    user =>
                        user.user_id === otherUserId
                );

            if (otherUser) {
                displayName =
                    otherUser.username;
            }
        }

        name.textContent =
            displayName;


        conversationRow.appendChild(icon);
        conversationRow.appendChild(name);

        conversationDiv.appendChild(
            conversationRow
        );
    });
}
function logout() {
    sessionStorage.clear();
    window.location.href = "Index.html";
}
function openUserChat(username) {
    console.log("OPEN USER CHAT CALLED:", username);

    const selectedUser =
        users.find(
            u => u.username === username
        );

    socket.send(JSON.stringify({
        type: "create_conversation",
        participant_ids: [
            selectedUser.user_id
        ]
    }));
}

renderContacts();