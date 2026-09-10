//Button

const loginbutton= document.getElementById("loginButton");

loginbutton.addEventListener("click",function(){
    const username= document.getElementById("username").value.trim();
    const serverIP= document.getElementById("serverIp").value.trim();
    const serverPort= document.getElementById("serverPort").value.trim();
    const password= document.getElementById("password").value.trim();
    const errorContainer= document.getElementById("empty");
    if(username===""||password===""|| serverIP===""|| serverPort===""){
        errorContainer.style.display='block';
        errorContainer.textContent="Fill in all the fields";
    }
    
    else if (password.length<8){
        errorContainer.style.display='block'
        errorContainer.textContent="password must be longer!"

    }
    else{
        sessionStorage.setItem("serverIp", serverIp);
        sessionStorage.setItem("serverPort", serverPort);
        sessionStorage.setItem("username", username);
        errorContainer.style.display='none';
        window.location.href="Chatlog.html";
    }
});
