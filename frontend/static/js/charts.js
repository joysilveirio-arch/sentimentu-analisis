const CHARTS = {
  colors: { Positive: "#16A34A", Negative: "#DC2626", Neutral: "#64748B", Unlabeled: "#F59E0B", primary: "#2563EB" },
  destroy(id) {
    const existing = Chart.getChart(id);
    if (existing) existing.destroy();
  },
  doughnut(id, labels, data) {
    this.destroy(id);
    const colors = labels.map(l => this.colors[l] || "#94A3B8");
    return new Chart(document.getElementById(id), {
      type: "doughnut",
      data: { labels, datasets: [{ data, backgroundColor: colors }] },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: "bottom" } } }
    });
  },
  line(id, labels, datasets) {
    this.destroy(id);
    return new Chart(document.getElementById(id), {
      type: "line",
      data: { labels, datasets },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: "bottom" } } }
    });
  },
  bar(id, labels, datasets) {
    this.destroy(id);
    return new Chart(document.getElementById(id), {
      type: "bar",
      data: { labels, datasets },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
    });
  },
  scatter(id, points, label) {
    this.destroy(id);
    return new Chart(document.getElementById(id), {
      type: "scatter",
      data: { datasets: [{ label: label || "", data: points, backgroundColor: "#2563EB" }] },
      options: { responsive: true, maintainAspectRatio: false }
    });
  }
};