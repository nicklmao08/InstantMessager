//Button
const loginbutton= document.getElementById("loginButton");
loginbutton.addEventListener("click",function(){
    const username= document.getElementById("username").value;
    const password= document.getElementById("password").value;
    if (username===""||password===""){
        document.getElementById("message").textContent=
        "Enter username and password:";
    } else{
        document.getElementById("message").textContent=
        "Logined in!"
    }

});