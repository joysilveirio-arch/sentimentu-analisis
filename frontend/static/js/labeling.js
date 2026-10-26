// Labeling module
// Assigns labels to records via API

const LABELING = {
  async assign(recordId, label) {
    if (!recordId || !label) throw new Error("Record ID and label required");
    const r = await API.post("/api/admin/labeling/assign", {
      record_id: recordId,
      label: label
    });
    if (!r.success) throw new Error(r.message);
    return r.data;
  },

  async listRecords(page = 1, perPage = 20) {
    const r = await API.get(`/api/data?page=${page}&per_page=${perPage}`);
    return r.data || [];
  },

  labels: ["Positive", "Neutral", "Negative"],

  renderTag(label) {
    return label ? `<span class="tag ${label}">${label}</span>` : "—";
  }
};