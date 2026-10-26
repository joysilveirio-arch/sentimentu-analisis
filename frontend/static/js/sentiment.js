// Sentiment analysis module
// Handles text analysis, bulk analyze, and wordlist fetch

const SENTIMENT = {
  async analyzeText(text) {
    if (!text || !text.trim()) throw new Error("Text required");
    const r = await API.post("/api/sentiment/analyze-text", { text });
    if (!r.success) throw new Error(r.message);
    return r.data;
  },

  async analyzeAll() {
    const r = await API.post("/api/admin/sentiment/analyze");
    if (!r.success) throw new Error(r.message);
    return r.data;
  },

  async wordlist() {
    const r = await API.get("/api/admin/wordlist");
    return r.data || [];
  },

  async addWord(word, sentiment, score = 1, language = "unknown") {
    const r = await API.post("/api/admin/wordlist", { word, sentiment, score, language });
    if (!r.success) throw new Error(r.message);
    return r.data;
  },

  async deleteWord(id) {
    const r = await API.del("/api/admin/wordlist/" + id);
    return r.success;
  },

  renderResult(data) {
    return `
      <div class="kpi-grid">
        <div class="kpi-card ${data.sentiment.toLowerCase()}">
          <div class="label">Sentiment</div>
          <div class="value">${data.sentiment}</div>
        </div>
        <div class="kpi-card">
          <div class="label">Score</div>
          <div class="value">${data.score}</div>
        </div>
        <div class="kpi-card positive">
          <div class="label">Positive Words</div>
          <div class="value">${data.positive}</div>
        </div>
        <div class="kpi-card negative">
          <div class="label">Negative Words</div>
          <div class="value">${data.negative}</div>
        </div>
      </div>
    `;
  }
};