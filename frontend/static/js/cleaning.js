// Data cleaning module — used by admin/cleaning.html
// Note: cleaning.html already has inline logic; this file is for reuse.

const CLEANING = {
  async run() {
    try {
      const r = await API.post("/api/admin/clean");
      if (r.success) {
        toast("Cleaning complete", "success");
        return r.data;
      }
      toast(r.message || "Cleaning failed", "error");
      return null;
    } catch (e) {
      toast(e.message, "error");
      return null;
    }
  },

  async history() {
    try {
      const r = await API.get("/api/admin/cleaning/history");
      return r.data;
    } catch (e) {
      toast(e.message, "error");
      return [];
    }
  },

  formatRow(row) {
    return `<tr>
      <td>${row.created_at || "—"}</td>
      <td>${row.original_records}</td>
      <td>${row.clean_records}</td>
      <td>${row.removed_records}</td>
      <td>${(row.quality_score || 0).toFixed(1)}%</td>
    </tr>`;
  }
};