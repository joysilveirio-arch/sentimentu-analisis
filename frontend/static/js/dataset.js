let currentPage = 1;

function escapeDatasetValue(value) {
  return String(value ?? "").replace(/[&<>"']/g, ch => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[ch]);
}

async function loadDataset(page = 1) {
  currentPage = page;
  const params = new URLSearchParams({ page, per_page: 20 });
  const s = document.getElementById("search").value.trim();
  if (s) params.set("search", s);
  const sent = document.getElementById("f-sentiment").value;
  if (sent) params.set("sentiment", sent);
  const g = document.getElementById("f-gender").value;
  if (g) params.set("gender", g);

  const box = document.getElementById("dataset-table");
  box.innerHTML = '<div class="loading">Loading...</div>';
  try {
    const r = await API.get("/api/data?" + params.toString());
    const { data, pagination } = r;
    if (!data.length) {
      box.innerHTML = '<div class="empty">No records found for current filters.</div>';
      document.getElementById("pagination").innerHTML = "";
      return;
    }

    let html = '<table class="dataset-table"><thead><tr><th>ID</th><th>Author</th><th class="dataset-original">Original Text</th><th class="dataset-cleaned">Cleaned Text</th><th>Sentiment</th><th>Gender</th><th>Date</th></tr></thead><tbody>';
    for (const row of data) {
      const sentiment = row.sentiment || "Unlabeled";
      const sentClass = ["Positive", "Negative", "Neutral", "Unlabeled"].includes(sentiment) ? sentiment : "Unlabeled";
      const original = row.text
        ? escapeDatasetValue(row.text)
        : '<span class="dataset-empty-badge">No original text</span>';
      let cleaned;
      if (row.cleaned_text === null || row.cleaned_text === undefined) {
        cleaned = '<span class="dataset-empty-badge">Seidauk iha testu limpu</span>';
      } else if (!String(row.cleaned_text).trim()) {
        cleaned = '<span class="dataset-empty-badge">Rezultadu mamuk</span>';
      } else {
        cleaned = escapeDatasetValue(row.cleaned_text);
      }

      html += `<tr>
        <td>${escapeDatasetValue(row.id)}</td>
        <td>${escapeDatasetValue(row.author_name || "—")}</td>
        <td class="dataset-text">${original}</td>
        <td class="dataset-text">${cleaned}</td>
        <td><span class="tag ${sentClass}">${escapeDatasetValue(sentiment)}</span></td>
        <td>${escapeDatasetValue(row.gender || "—")}</td>
        <td>${escapeDatasetValue(row.date ? row.date.slice(0,10) : "—")}</td>
      </tr>`;
    }
    html += "</tbody></table>";
    box.innerHTML = html;

    let pag = "";
    for (let i = 1; i <= pagination.pages; i++) {
      pag += `<button class="btn btn-ghost btn-sm ${i === page ? 'btn' : ''}" onclick="loadDataset(${i})">${i}</button>`;
    }
    document.getElementById("pagination").innerHTML = pag;
  } catch (e) {
    box.innerHTML = `<div class="empty">Error: ${escapeDatasetValue(e.message)}</div>`;
  }
}
function applyFilters() { loadDataset(1); }
function resetFilters() {
  document.getElementById("search").value = "";
  document.getElementById("f-sentiment").value = "";
  document.getElementById("f-gender").value = "";
  loadDataset(1);
}
document.addEventListener("DOMContentLoaded", () => loadDataset(1));
