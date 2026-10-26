const API = {
  async request(path, options = {}) {
    const res = await fetch(path, {
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      ...options,
    });
    const data = await res.json().catch(() => ({ success: false, message: "Invalid response" }));
    if (!res.ok) throw new Error(data.message || `HTTP ${res.status}`);
    return data;
  },
  get(path) { return this.request(path); },
  post(path, body) { return this.request(path, { method: "POST", body: JSON.stringify(body || {}) }); },
  put(path, body) { return this.request(path, { method: "PUT", body: JSON.stringify(body || {}) }); },
  del(path) { return this.request(path, { method: "DELETE" }); },
  async upload(path, file) {
    const fd = new FormData();
    fd.append("file", file);
    const res = await fetch(path, { method: "POST", body: fd, credentials: "same-origin" });
    return res.json();
  }
};

function toast(msg, type = "info") {
  const t = document.createElement("div");
  t.className = `toast ${type}`;
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 3000);
}

async function logout() {
  await API.post("/api/auth/logout");
  window.location.href = "/login";
}

async function loadCurrentUser() {
  try {
    const r = await API.get("/api/auth/me");
    return r.data;
  } catch { return null; }
}