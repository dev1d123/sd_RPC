const calcForm = document.getElementById("calcForm");
const calcA = document.getElementById("calcA");
const calcB = document.getElementById("calcB");
const calcOp = document.getElementById("calcOp");
const calcResult = document.getElementById("calcResult");

const chatForm = document.getElementById("chatForm");
const chatUser = document.getElementById("chatUser");
const chatMsg = document.getElementById("chatMsg");
const chatList = document.getElementById("chatList");

const API_BASE = "http://localhost:5000/api";

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return response.json();
}

async function fetchJson(url) {
  const response = await fetch(url);
  return response.json();
}

calcForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const a = Number(calcA.value);
  const b = Number(calcB.value);
  const op = calcOp.value;

  calcResult.textContent = "Working...";
  try {
    const data = await postJson(`${API_BASE}/calc`, {
      op,
      params: [a, b],
    });
    if (data.ok) {
      calcResult.textContent = `Result: ${data.result}`;
    } else {
      calcResult.textContent = `Error: ${data.error}`;
    }
  } catch (err) {
    calcResult.textContent = "Error: request failed";
  }
});

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const user = chatUser.value.trim();
  const msg = chatMsg.value.trim();
  if (!user || !msg) {
    return;
  }

  try {
    await postJson(`${API_BASE}/chat/send`, { user, msg });
    chatMsg.value = "";
    await refreshChat();
  } catch (err) {
    console.error(err);
  }
});

function renderChat(messages) {
  chatList.innerHTML = "";
  messages.forEach((message) => {
    const item = document.createElement("div");
    item.className = "chat-item";

    const user = document.createElement("span");
    user.className = "user";
    user.textContent = message.user;

    const msg = document.createElement("span");
    msg.textContent = message.msg;

    const time = document.createElement("span");
    time.className = "time";
    time.textContent = message.ts || "";

    item.appendChild(user);
    item.appendChild(msg);
    item.appendChild(time);

    chatList.appendChild(item);
  });
}

async function refreshChat() {
  try {
    const data = await fetchJson(`${API_BASE}/chat/list?limit=50`);
    if (data.ok) {
      renderChat(data.messages || []);
    }
  } catch (err) {
    console.error(err);
  }
}

refreshChat();
setInterval(refreshChat, 4000);
