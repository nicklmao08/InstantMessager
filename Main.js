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
const addcontact= document.getElementById(addcontact);
const chatListContainer=document.querySelector('chatlistcontainer');
addcontact.addEventListener('click',()=>{
    const newRow=document.createElement('div');
    newRow.classList.add('chat-row');
    newRow.setAttribute('name','Lemao lol')
    

})