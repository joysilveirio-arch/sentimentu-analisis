async function loadDashboard() {
  try {
    const ov = await API.get("/api/dashboard/overview");
    document.getElementById("kpi-records").textContent = ov.data.total_records;
    document.getElementById("kpi-likes").textContent = ov.data.total_likes;
    document.getElementById("kpi-comments").textContent = ov.data.total_comments;
    document.getElementById("kpi-positive").textContent = ov.data.positive;
    document.getElementById("kpi-negative").textContent = ov.data.negative;
    document.getElementById("kpi-neutral").textContent = ov.data.neutral;
    document.getElementById("kpi-unlabeled").textContent = ov.data.unlabeled;

    const sd = await API.get("/api/dashboard/sentiment");
    CHARTS.doughnut("chart-sentiment", sd.data.map(x => x.label), sd.data.map(x => x.value));

    const tr = await API.get("/api/dashboard/trends");
    const labels = tr.data.map(x => x.date);
    CHARTS.line("chart-trend", labels, [
      { label: "Positive", data: tr.data.map(x => x.Positive), borderColor: "#16A34A", tension: 0.3 },
      { label: "Negative", data: tr.data.map(x => x.Negative), borderColor: "#DC2626", tension: 0.3 },
      { label: "Neutral", data: tr.data.map(x => x.Neutral), borderColor: "#64748B", tension: 0.3 },
      { label: "Unlabeled", data: tr.data.map(x => x.Unlabeled), borderColor: "#F59E0B", tension: 0.3 },
    ]);

    const en = await API.get("/api/dashboard/engagement");
    CHARTS.line("chart-engagement", en.data.map(x => x.date), [
      { label: "Likes", data: en.data.map(x => x.likes), borderColor: "#2563EB", tension: 0.3 },
      { label: "Comments", data: en.data.map(x => x.comments), borderColor: "#F59E0B", tension: 0.3 },
    ]);

    const gd = await API.get("/api/dashboard/gender");
    CHARTS.doughnut("chart-gender", gd.data.map(x => x.label), gd.data.map(x => x.value));

    const au = await API.get("/api/dashboard/authors");
    CHARTS.bar("chart-authors", au.data.map(x => x.name), [{ label: "Comments", data: au.data.map(x => x.count), backgroundColor: "#2563EB" }]);
  } catch (e) {
    toast("Dashboard: " + e.message, "error");
  }
}
document.addEventListener("DOMContentLoaded", loadDashboard);
