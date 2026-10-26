// Admin module — users, import, wordlist, labels, database, history

const ADMIN = {
  // ===== USERS =====
  async listUsers() {
    const r = await API.get("/api/admin/users");
    return r.data || [];
  },
  async createUser(payload) {
    const r = await API.post("/api/admin/users", payload);
    if (!r.success) throw new Error(r.message);
    return r.data;
  },
  async updateUser(id, payload) {
    const r = await API.put("/api/admin/users/" + id, payload);
    if (!r.success) throw new Error(r.message);
    return r.data;
  },
  async deleteUser(id) {
    const r = await API.del("/api/admin/users/" + id);
    if (!r.success) throw new Error(r.message);
    return true;
  },

  // ===== IMPORT =====
  async importCsv(file) {
    const r = await API.upload("/api/admin/import", file);
    if (!r.success) throw new Error(r.message);
    return r.data;
  },
  async importHistory() {
    const r = await API.get("/api/admin/import/history");
    return r.data || [];
  },

  // ===== CLEANING =====
  async clean() {
    const r = await API.post("/api/admin/clean");
    if (!r.success) throw new Error(r.message);
    return r.data;
  },
  async cleaningHistory() {
    const r = await API.get("/api/admin/cleaning/history");
    return r.data || [];
  },

  // ===== WORDLIST =====
  async listWords() {
    const r = await API.get("/api/admin/wordlist");
    return r.data || [];
  },
  async createWord(payload) {
    const r = await API.post("/api/admin/wordlist", payload);
    if (!r.success) throw new Error(r.message);
    return r.data;
  },
  async updateWord(id, payload) {
    const r = await API.put("/api/admin/wordlist/" + id, payload);
    if (!r.success) throw new Error(r.message);
    return r.data;
  },
  async deleteWord(id) {
    const r = await API.del("/api/admin/wordlist/" + id);
    return r.success;
  },

  // ===== LABELS =====
  async listLabels() {
    const r = await API.get("/api/admin/labels");
    return r.data || [];
  },
  async createLabel(payload) {
    const r = await API.post("/api/admin/labels", payload);
    if (!r.success) throw new Error(r.message);
    return r.data;
  },
  async updateLabel(id, payload) {
    const r = await API.put("/api/admin/labels/" + id, payload);
    if (!r.success) throw new Error(r.message);
    return r.data;
  },
  async deleteLabel(id) {
    const r = await API.del("/api/admin/labels/" + id);
    return r.success;
  },

  // ===== DATABASE =====
  async dbInfo() {
    const r = await API.get("/api/admin/database/info");
    return r.data;
  },

  // ===== AUDIT =====
  async audit() {
    const r = await API.get("/api/admin/audit");
    return r.data || [];
  }
};