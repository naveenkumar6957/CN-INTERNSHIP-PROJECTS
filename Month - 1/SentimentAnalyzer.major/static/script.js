const API_BASE = "";

const searchForm = document.getElementById("search-form");
const sourceSelect = document.getElementById("source-select");
const urlField = document.getElementById("url-field");
const searchBtn = document.getElementById("search-btn");

const emptyState = document.getElementById("empty-state");
const dashboard = document.getElementById("dashboard");
const loading = document.getElementById("loading");
const errorBox = document.getElementById("error-box");

const productList = document.getElementById("product-list");
const reviewsList = document.getElementById("reviews-list");
const filterGroup = document.getElementById("filter-group");

let currentReviews = [];
let currentFilter = "all";
let charts = {};

sourceSelect.addEventListener("change", () => {
  urlField.classList.toggle("hidden", sourceSelect.value !== "url");
});

searchForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const productName = document.getElementById("product-name").value.trim();
  const source = sourceSelect.value;
  const url = document.getElementById("product-url").value.trim();

  if (!productName) return;

  setLoading(true);
  hideError();

  try {
    const res = await fetch(`${API_BASE}/api/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ product_name: productName, source, url })
    });
    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.error || "Something went wrong while collecting reviews.");
    }

    await loadDashboard(data.product_id);
    await refreshProductList();
  } catch (err) {
    showError(err.message);
  } finally {
    setLoading(false);
  }
});

filterGroup.addEventListener("click", (e) => {
  const btn = e.target.closest(".filter-btn");
  if (!btn) return;
  currentFilter = btn.dataset.filter;
  [...filterGroup.children].forEach(b => b.classList.toggle("active", b === btn));
  renderReviews();
});

async function loadDashboard(productId) {
  const [summaryRes, reviewsRes] = await Promise.all([
    fetch(`${API_BASE}/api/sentiment-summary/${productId}`),
    fetch(`${API_BASE}/api/reviews/${productId}`)
  ]);

  const summary = await summaryRes.json();
  const reviewsData = await reviewsRes.json();

  if (!summaryRes.ok) throw new Error(summary.error || "Could not load summary.");
  if (!reviewsRes.ok) throw new Error(reviewsData.error || "Could not load reviews.");

  currentReviews = reviewsData.reviews;
  currentFilter = "all";
  [...filterGroup.children].forEach(b => b.classList.toggle("active", b.dataset.filter === "all"));

  renderHero(summary);
  renderDistributionChart(summary.sentiment_counts);
  renderTrendChart(summary.sentiment_trend);
  renderWordChart(summary.word_frequency);
  renderReviews();

  emptyState.classList.add("hidden");
  dashboard.classList.remove("hidden");
}

function renderHero(summary) {
  const total = summary.total_reviews;
  const counts = summary.sentiment_counts;
  const positivePct = total ? Math.round((counts.positive / total) * 100) : 0;

  document.getElementById("hero-percent").textContent = `${positivePct}%`;
  document.getElementById("hero-product-name").textContent = summary.product.name;
  document.getElementById("stat-total").textContent = total;
  document.getElementById("stat-rating").textContent =
    summary.average_rating !== null ? `${summary.average_rating} / 5` : "N/A";
  document.getElementById("stat-negative").textContent = counts.negative;
}

function renderDistributionChart(counts) {
  const ctx = document.getElementById("chart-distribution");
  destroyChart("distribution");

  charts.distribution = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: ["Positive", "Neutral", "Negative"],
      datasets: [{
        data: [counts.positive, counts.neutral, counts.negative],
        backgroundColor: ["#3E7C5A", "#B08D3E", "#B23A2E"],
        borderWidth: 0
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: { position: "bottom", labels: { font: { family: "IBM Plex Sans", size: 12.5 }, boxWidth: 10 } }
      }
    }
  });
}

function renderTrendChart(trend) {
  const ctx = document.getElementById("chart-trend");
  destroyChart("trend");

  charts.trend = new Chart(ctx, {
    type: "line",
    data: {
      labels: trend.map(t => t.date),
      datasets: [
        { label: "Positive", data: trend.map(t => t.positive), borderColor: "#3E7C5A", backgroundColor: "#3E7C5A", tension: 0.3 },
        { label: "Neutral", data: trend.map(t => t.neutral), borderColor: "#B08D3E", backgroundColor: "#B08D3E", tension: 0.3 },
        { label: "Negative", data: trend.map(t => t.negative), borderColor: "#B23A2E", backgroundColor: "#B23A2E", tension: 0.3 }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: { position: "bottom", labels: { font: { family: "IBM Plex Sans", size: 12.5 }, boxWidth: 10 } }
      },
      scales: {
        x: { ticks: { font: { size: 10.5 } } },
        y: { beginAtZero: true, ticks: { precision: 0 } }
      }
    }
  });
}

function renderWordChart(wordFreq) {
  const ctx = document.getElementById("chart-words");
  destroyChart("words");

  charts.words = new Chart(ctx, {
    type: "bar",
    data: {
      labels: wordFreq.map(w => w.word),
      datasets: [{
        label: "Mentions",
        data: wordFreq.map(w => w.count),
        backgroundColor: "#2F5D50"
      }]
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: true,
      plugins: { legend: { display: false } },
      scales: {
        x: { beginAtZero: true, ticks: { precision: 0 } }
      }
    }
  });
}

function destroyChart(key) {
  if (charts[key]) {
    charts[key].destroy();
    delete charts[key];
  }
}

function renderReviews() {
  const filtered = currentFilter === "all"
    ? currentReviews
    : currentReviews.filter(r => r.sentiment_label === currentFilter);

  reviewsList.innerHTML = "";

  if (filtered.length === 0) {
    reviewsList.innerHTML = `<li class="review-item"><div class="review-body"><p>No reviews in this category.</p></div></li>`;
    return;
  }

  filtered.slice(0, 40).forEach(r => {
    const li = document.createElement("li");
    li.className = "review-item";
    li.innerHTML = `
      <span class="review-tag ${r.sentiment_label}"></span>
      <div class="review-body">
        <p>${escapeHtml(r.review_text)}</p>
        <div class="review-meta">
          ${r.review_date || ""} ${r.rating ? `&middot; ${r.rating} / 5 rating` : ""} &middot; ${r.sentiment_label}
        </div>
      </div>
    `;
    reviewsList.appendChild(li);
  });
}

async function refreshProductList() {
  const res = await fetch(`${API_BASE}/api/products`);
  const products = await res.json();

  productList.innerHTML = "";
  products.forEach(p => {
    const li = document.createElement("li");
    const btn = document.createElement("button");
    btn.textContent = p.name;
    btn.addEventListener("click", () => loadDashboard(p.id));
    li.appendChild(btn);
    productList.appendChild(li);
  });
}

function setLoading(isLoading) {
  loading.classList.toggle("hidden", !isLoading);
  searchBtn.disabled = isLoading;
  searchBtn.textContent = isLoading ? "Analyzing..." : "Analyze reviews";
  if (isLoading) {
    emptyState.classList.add("hidden");
  }
}

function showError(message) {
  errorBox.textContent = message;
  errorBox.classList.remove("hidden");
  if (dashboard.classList.contains("hidden")) {
    emptyState.classList.remove("hidden");
  }
}

function hideError() {
  errorBox.classList.add("hidden");
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

refreshProductList();
