//Button
const loginbutton= document.getElementById("loginButton");
loginbutton.addEventListener("click",function(){
    const username= document.getElementById("username").value;
    const password= document.getElementById("password").value;
    const errorContainer= document.getElementById("empty");
    if(username===""||password===""){
        errorContainer.style.display='block';
        errorContainer.textContent="Username or password is empty";
    }
    
    else if (password.length<12){
        errorContainer.style.display='block'
        errorContainer.textContent="password must be longer!"

    }
    else{
        errorContainer.style.display='none';
        window.location.href="Chatlog.html";
    }

});
//Add contact button
let currentcontact=null;

let conversations={
    Mom:[{
        text:"lu udh makan?",
        type:"recieved"
    }
    ],
    Dad:[{
        text:"udh kirim uang ya",
        type:"recieved"
    }]
}
function openChat(contactName) {

    currentContact = contactName;

    document.getElementById("contactName").textContent =
        contactName;

    displayMessages();
}
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