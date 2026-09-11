//Button

const loginbutton= document.getElementById("loginButton");

loginbutton.addEventListener("click",function(){
    const username= document.getElementById("username").value.trim();
    const password= document.getElementById("password").value.trim();
    const errorContainer= document.getElementById("empty");
    if(username===""||password===""){
        errorContainer.style.display='block';
        errorContainer.textContent="Fill in all the fields";
    }
    
    else if (password.length<8){
        errorContainer.style.display='block'
        errorContainer.textContent="password must be longer!"

    }
    else{
        sessionStorage.setItem("username", username);
        errorContainer.style.display='none';
        window.location.href="Chatlog.html";
    }
});
