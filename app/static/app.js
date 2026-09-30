const $ = (id) => document.getElementById(id);

async function loadDocuments() {
  const res = await fetch("/documents");
  const data = await res.json();
  const list = $("docList");
  list.innerHTML = "";
  if (!data.documents.length) {
    list.innerHTML = '<li class="muted">No documents yet.</li>';
    return;
  }
  for (const doc of data.documents) {
    const li = document.createElement("li");
    const left = document.createElement("span");
    left.textContent = doc.filename;
    const meta = document.createElement("span");
    meta.className = "meta";
    meta.textContent = `${doc.chunks} chunks`;
    left.appendChild(meta);
    const btn = document.createElement("button");
    btn.textContent = "Delete";
    btn.onclick = async () => {
      await fetch(`/documents/${doc.id}`, { method: "DELETE" });
      loadDocuments();
    };
    li.appendChild(left);
    li.appendChild(btn);
    list.appendChild(li);
  }
}

$("uploadBtn").onclick = async () => {
  const input = $("fileInput");
  const status = $("uploadStatus");
  if (!input.files.length) {
    status.textContent = "Please choose a file first.";
    return;
  }
  const form = new FormData();
  form.append("file", input.files[0]);
  $("uploadBtn").disabled = true;
  status.textContent = "Uploading and indexing...";
  try {
    const res = await fetch("/documents", { method: "POST", body: form });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Upload failed");
    status.textContent = `Indexed "${data.filename}" (${data.chunks} chunks).`;
    input.value = "";
    loadDocuments();
  } catch (err) {
    status.textContent = "Error: " + err.message;
  } finally {
    $("uploadBtn").disabled = false;
  }
};

function addMessage(who, text, sources) {
  const chat = $("chat");
  const div = document.createElement("div");
  div.className = "msg " + (who === "You" ? "user" : "bot");
  const label = document.createElement("span");
  label.className = "who";
  label.textContent = who;
  div.appendChild(label);
  div.appendChild(document.createTextNode(text));
  if (sources && sources.length) {
    const details = document.createElement("details");
    details.className = "sources";
    const summary = document.createElement("summary");
    summary.textContent = `Sources (${sources.length})`;
    details.appendChild(summary);
    for (const s of sources) {
      const box = document.createElement("div");
      box.className = "source";
      const head = document.createElement("div");
      head.className = "shead";
      head.textContent = `${s.filename} · chunk ${s.chunk_index} · score ${s.score}`;
      box.appendChild(head);
      box.appendChild(document.createTextNode(s.text));
      details.appendChild(box);
    }
    div.appendChild(details);
  }
  chat.appendChild(div);
  div.scrollIntoView({ behavior: "smooth", block: "end" });
}

async function ask() {
  const input = $("questionInput");
  const question = input.value.trim();
  if (!question) return;
  addMessage("You", question);
  input.value = "";
  $("askBtn").disabled = true;
  try {
    const res = await fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Request failed");
    addMessage("Assistant", data.answer, data.sources);
  } catch (err) {
    addMessage("Assistant", "Error: " + err.message);
  } finally {
    $("askBtn").disabled = false;
  }
}

$("askBtn").onclick = ask;
$("questionInput").addEventListener("keydown", (e) => {
  if (e.key === "Enter") ask();
});

loadDocuments();
