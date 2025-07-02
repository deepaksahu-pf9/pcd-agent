// Chat submission
document.getElementById("chat-form").addEventListener("submit", async function (e) {
  e.preventDefault();
  const input = document.getElementById("user-input");
  const query = input.value.trim();
  const selectedModel = document.getElementById("gpt-model").value;
  const maxTokens = document.getElementById("max-tokens").value;

  console.log("🧠 Selected GPT Model:", selectedModel);
  console.log("🔢 Max Tokens:", maxTokens);

  if (!query) return;

  appendMessage("user", query);
  input.value = "";

  const loader = document.getElementById("chat-loader");
  loader.style.display = "block";

  try {
    const res = await fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });

    const data = await res.json();
    appendMessage("agent", data.response);
  } catch (err) {
    appendMessage("agent", "❌ Failed to connect to the server.");
    console.error("Fetch error:", err);
  } finally {
    loader.style.display = "none";
  }
});

// Append message to chat window
function appendMessage(role, text) {
  const container = document.getElementById("chat-window");
  const messageBlock = document.createElement("div");
  messageBlock.className = `message-block ${role}-message`;
  messageBlock.textContent = text;
  container.appendChild(messageBlock);
  container.scrollTop = container.scrollHeight;
}

// Save GPT Model + Max Tokens (UI only)
document.getElementById("gpt-save-btn")?.addEventListener("click", () => {
  const model = document.getElementById("gpt-model").value;
  const tokens = document.getElementById("max-tokens").value;
  alert(`✅ GPT settings updated:\nModel: ${model}\nMax Tokens: ${tokens}`);
});

// Kubeconfig modal logic
const kubeModal = document.getElementById("kubeconfig-modal");
const setKubeBtn = document.getElementById("set-kubeconfig-btn");
const cancelKubeBtn = document.getElementById("cancel-kubeconfig-btn");
const saveKubeBtn = document.getElementById("save-kubeconfig-btn");

setKubeBtn.addEventListener("click", () => {
  kubeModal.style.display = "flex";
});

cancelKubeBtn.addEventListener("click", () => {
  kubeModal.style.display = "none";
});

saveKubeBtn.addEventListener("click", async () => {
  const kubeconfig = document.getElementById("kubeconfig-input").value.trim();
  if (!kubeconfig) {
    alert("Please paste your kubeconfig.");
    return;
  }

  try {
    const res = await fetch("/set-kubeconfig", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ kubeconfig }),
    });

    const data = await res.json();
    appendMessage("agent", data.message || "✅ Kubeconfig saved.");
    kubeModal.style.display = "none";
  } catch (err) {
    appendMessage("agent", "❌ Failed to save kubeconfig.");
    console.error("Kubeconfig save error:", err);
  }
});

// SSH Key modal logic
const sshModal = document.getElementById("sshkey-modal");
const setSSHBtn = document.getElementById("set-sshkey-btn");
const cancelSSHBtn = document.getElementById("cancel-sshkey-btn");
const saveSSHBtn = document.getElementById("save-sshkey-btn");

setSSHBtn.addEventListener("click", () => {
  sshModal.style.display = "flex";
});

cancelSSHBtn.addEventListener("click", () => {
  sshModal.style.display = "none";
});

saveSSHBtn.addEventListener("click", async () => {
  const sshKey = document.getElementById("sshkey-input").value.trim();
  if (!sshKey) {
    alert("Please paste your SSH key.");
    return;
  }

  try {
    const res = await fetch("/set-ssh-key", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ssh_key: sshKey }),
    });

    const data = await res.json();
    appendMessage("agent", data.message || "✅ SSH key saved.");
    sshModal.style.display = "none";
  } catch (err) {
    appendMessage("agent", "❌ Failed to save SSH key.");
    console.error("SSH key save error:", err);
  }
});

// Save SSH IP
document.getElementById("ssh-ip-form").addEventListener("submit", async function (e) {
  e.preventDefault();
  const sshIp = document.getElementById("ssh-ip").value.trim();
  if (!sshIp) {
    alert("Please enter SSH IP.");
    return;
  }

  try {
    const res = await fetch("/set-ssh-ip", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ssh_ip: sshIp }),
    });

    const data = await res.json();
    appendMessage("agent", data.message || "✅ SSH IP saved.");
  } catch (err) {
    appendMessage("agent", "❌ Failed to save SSH IP.");
    console.error("SSH IP save error:", err);
  }
});

// OpenAI API Key modal logic
const openaiModal = document.getElementById("openai-modal");
const setOpenaiBtn = document.getElementById("set-openai-btn");
const cancelOpenaiBtn = document.getElementById("cancel-openai-btn");
const saveOpenaiBtn = document.getElementById("save-openai-btn");

setOpenaiBtn.addEventListener("click", () => {
  openaiModal.style.display = "flex";
});

cancelOpenaiBtn.addEventListener("click", () => {
  openaiModal.style.display = "none";
});

saveOpenaiBtn.addEventListener("click", async () => {
  const openaiKey = document.getElementById("openai-input").value.trim();
  if (!openaiKey || !openaiKey.startsWith("sk-")) {
    alert("Please enter a valid OpenAI API key.");
    return;
  }

  try {
    const res = await fetch("/set-openai-key", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ api_key: openaiKey }),
    });

    const data = await res.json();
    appendMessage("agent", data.message || "✅ OpenAI API key saved.");
    openaiModal.style.display = "none";
  } catch (err) {
    appendMessage("agent", "❌ Failed to save OpenAI key.");
    console.error("OpenAI key save error:", err);
  }
});
