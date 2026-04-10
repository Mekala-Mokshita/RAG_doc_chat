const API = "http://127.0.0.1:8000";

/* ===== MULTI CHAT STORAGE ===== */
let chats = JSON.parse(localStorage.getItem("allChats")) || {};
let currentChatId = localStorage.getItem("currentChat") || Date.now().toString();

/* ================= INIT ================= */

document.addEventListener("DOMContentLoaded", () => {

    const token = localStorage.getItem("token");

    if (!token) {
        window.location.href = "/";
        return;
    }

    // show username
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        document.getElementById("userDisplay").innerText = "👤 " + payload.sub;
    } catch {
        logout();
    }

    // load sidebar + chat
    renderHistory();
    loadChat(currentChatId);

    // events
    document.getElementById("uploadBtn")?.addEventListener("click", uploadPDF);
    document.getElementById("askBtn")?.addEventListener("click", askQuestion);

    // ENTER key
    document.getElementById("question")?.addEventListener("keypress", (e) => {
        if (e.key === "Enter") askQuestion();
    });

    // ===== DRAG & DROP =====
    const dropArea = document.getElementById("dropArea");

    if(dropArea){
        dropArea.addEventListener("dragover", (e)=>{
            e.preventDefault();
            dropArea.style.borderColor = "#2563eb";
        });

        dropArea.addEventListener("dragleave", ()=>{
            dropArea.style.borderColor = "#334155";
        });

        dropArea.addEventListener("drop", (e)=>{
            e.preventDefault();
            const file = e.dataTransfer.files[0];

            if(file && file.type === "application/pdf"){
                document.getElementById("pdfFile").files = e.dataTransfer.files;
                showToast("📄 File selected");
            } else {
                showToast("❌ Only PDF allowed");
            }
        });
    }
});


/* ================= LOGOUT ================= */

function logout(){
    localStorage.removeItem("token");
    window.location.href="/";
}


/* ================= SIDEBAR ================= */

function newChat(){
    currentChatId = Date.now().toString();
    localStorage.setItem("currentChat", currentChatId);

    chats[currentChatId] = [];
    localStorage.setItem("allChats", JSON.stringify(chats));

    document.getElementById("chatbox").innerHTML = "";
    renderHistory();
}

function saveMessage(text, type){
    if(!chats[currentChatId]) chats[currentChatId] = [];

    chats[currentChatId].push({text, type});
    localStorage.setItem("allChats", JSON.stringify(chats));
}

function loadChat(id){
    currentChatId = id;
    localStorage.setItem("currentChat", id);

    const chatbox = document.getElementById("chatbox");
    chatbox.innerHTML = "";

    (chats[id] || []).forEach(msg=>{
        const div = document.createElement("div");
        div.className = msg.type;
        div.innerHTML = msg.text;
        chatbox.appendChild(div);
    });
}

function renderHistory(){
    const list = document.getElementById("historyList");
    if(!list) return;

    list.innerHTML = "";

    Object.keys(chats).forEach(id=>{
        const item = document.createElement("div");
        item.className = "history-item";
        item.innerText = "Chat " + id.slice(-4);
        item.onclick = ()=>loadChat(id);
        list.appendChild(item);
    });
}


/* ================= HELPERS ================= */

function addMessage(text, type="bot") {
    const chatbox = document.getElementById("chatbox");

    const div = document.createElement("div");
    div.className = type;
    div.innerHTML = text;

    chatbox.appendChild(div);
    chatbox.scrollTop = chatbox.scrollHeight;

    saveMessage(text, type);
    renderHistory();
}

// typing effect
function typeEffect(text, element){
    let i = 0;
    const interval = setInterval(()=>{
        element.innerHTML += text[i];
        i++;
        if(i>=text.length) clearInterval(interval);
    },15);
}


/* ================= UPLOAD ================= */

async function uploadPDF(){

    const fileInput = document.getElementById("pdfFile");
    const file = fileInput.files[0];

    if(!file){
        showToast("⚠️ Please select a PDF first");
        return;
    }

    const token = localStorage.getItem("token");

    const formData = new FormData();
    formData.append("file", file);

    document.getElementById("status").innerText =
        "⏳ Uploading & processing document...";

    try{

        const response = await fetch(`${API}/upload`,{
            method:"POST",
            headers:{
                "Authorization":`Bearer ${token}`
            },
            body:formData
        });

        if(response.status===401){
            showToast("Session expired. Login again.");
            logout();
            return;
        }

        const data = await response.json();

        document.getElementById("status").innerText = data.message;

        document.getElementById("question").disabled=false;
        document.getElementById("askBtn").disabled=false;

        addMessage("📄 Document ready! Ask your questions.", "bot");

        showToast("✅ PDF uploaded successfully");

    }catch(err){
        console.error(err);
        showToast("❌ Upload failed");
    }
}


/* ================= ASK ================= */

async function askQuestion(){

    const input = document.getElementById("question");
    const q = input.value.trim();

    if(!q) return;

    const token = localStorage.getItem("token");

    // user message (clean)
    addMessage(q, "user");
    input.value = "";

    const chatbox = document.getElementById("chatbox");

    const loadingDiv = document.createElement("div");
    loadingDiv.className = "bot";
    loadingDiv.innerText = "🤖 Thinking...";
    chatbox.appendChild(loadingDiv);

    try{

        const response = await fetch(`${API}/ask?query=${encodeURIComponent(q)}`,{
            headers:{
                "Authorization":`Bearer ${token}`
            }
        });

        loadingDiv.remove();

        if(response.status===401){
            showToast("Session expired. Login again.");
            logout();
            return;
        }

        const data = await response.json();

        const botDiv = document.createElement("div");
        botDiv.className = "bot";
        chatbox.appendChild(botDiv);

        // only answer (no label)
        typeEffect(data.answer, botDiv);

    }catch(err){
        loadingDiv.remove();
        console.error(err);
        addMessage("❌ Error getting response", "bot");
    }
}


/* ================= TOAST ================= */

function showToast(msg){
    const toast = document.getElementById("toast");
    toast.innerText = msg;
    toast.classList.add("show");

    setTimeout(()=>{
        toast.classList.remove("show");
    }, 2500);
}