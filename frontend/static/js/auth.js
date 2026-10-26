// Auth helpers — extended from api.js
// Handles login state, redirect, and role checks

const AUTH = {
  async login(username, password) {
    const r = await API.post("/api/auth/login", { username, password });
    if (r.success) window.location.href = "/dashboard";
    return r;
  },

  async logout() {
    await API.post("/api/auth/logout");
    window.location.href = "/login";
  },

  async me() {
    try {
      const r = await API.get("/api/auth/me");
      return r.data;
    } catch { return null; }
  },

  async isAdmin() {
    const u = await this.me();
    return u && u.role === "ADMIN";
  },

  async requireAuth(redirectTo = "/login") {
    const u = await this.me();
    if (!u) window.location.href = redirectTo;
    return u;
  },

  async requireAdmin() {
    const u = await this.requireAuth();
    if (u && u.role !== "ADMIN") {
      toast("Admin privilege required", "error");
      window.location.href = "/dashboard";
    }
    return u;
  }
};