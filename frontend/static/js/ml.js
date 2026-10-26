// ML module — train, evaluate, predict

const ML = {
  async train(config = {}) {
    const payload = {
      max_depth: config.max_depth ?? 15,
      test_size: config.test_size ?? 0.2,
      max_features: config.max_features ?? 5000,
    };
    const r = await API.post("/api/admin/ml/train", payload);
    if (!r.success) throw new Error(r.message);
    return r.history;
  },

  async history() {
    const r = await API.get("/api/admin/ml/history");
    return r.data || [];
  },

  async evaluation() {
    const r = await API.get("/api/admin/ml/evaluation");
    if (!r.success) throw new Error(r.message);
    return r.data;
  },

  async predict(text) {
    if (!text || !text.trim()) throw new Error("Text required");
    const r = await API.post("/api/predict", { text });
    if (!r.success) throw new Error(r.message);
    return r;
  },

  async predictBatch(texts) {
    const r = await API.post("/api/predict/batch", { texts });
    return r.data || [];
  },

  renderMetrics(history) {
    return `
      <div class="kpi-grid">
        <div class="kpi-card"><div class="label">Accuracy</div><div class="value">${(history.accuracy*100).toFixed(2)}%</div></div>
        <div class="kpi-card"><div class="label">Precision</div><div class="value">${(history.precision*100).toFixed(2)}%</div></div>
        <div class="kpi-card"><div class="label">Recall</div><div class="value">${(history.recall*100).toFixed(2)}%</div></div>
        <div class="kpi-card"><div class="label">F1 Score</div><div class="value">${(history.f1_score*100).toFixed(2)}%</div></div>
      </div>
    `;
  }
};