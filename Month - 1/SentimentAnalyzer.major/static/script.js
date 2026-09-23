const API_BASE = "";

// DOM Elements
const searchForm = document.getElementById("search-form");
const productQueryInput = document.getElementById("product-query");
const searchBtn = document.getElementById("search-btn");
const platformBtns = document.querySelectorAll(".platform-btn");

const emptyState = document.getElementById("empty-state");
const loadingState = document.getElementById("loading");
const errorBox = document.getElementById("error-box");
const dashboard = document.getElementById("dashboard");

const productList = document.getElementById("product-list");
const historyCount = document.getElementById("history-count");
const reviewsList = document.getElementById("reviews-list");
const reviewSearchInput = document.getElementById("review-search-input");

const filterSentimentGroup = document.getElementById("filter-sentiment");
const filterPlatformGroup = document.getElementById("filter-platform");

const exportBtn = document.getElementById("export-btn");
const deleteBtn = document.getElementById("delete-btn");

// State
let selectedPlatform = "both";
let currentProductId = null;
let currentReviews = [];
let currentSentimentFilter = "all";
let currentPlatformFilter = "all";
let currentSearchTerm = "";
let charts = {};

// Platform Toggle Listener
platformBtns.forEach(btn => {
  btn.addEventListener("click", () => {
    platformBtns.forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    selectedPlatform = btn.dataset.platform;
  });
});

// Sample Pill Listeners
document.querySelectorAll(".sample-pill").forEach(pill => {
  pill.addEventListener("click", () => {
    productQueryInput.value = pill.dataset.query;
    searchForm.dispatchEvent(new Event("submit"));
  });
});

// Search Form Submit
searchForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const query = productQueryInput.value.trim();
  if (!query) return;

  setLoading(true, `Collecting Reviews for "${query}"`);
  hideError();

  try {
    const res = await fetch(`${API_BASE}/api/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: query, platform: selectedPlatform })
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || "Failed to analyze product reviews.");
    }

    currentProductId = data.product_id;
    await loadDashboard(currentProductId);
    await refreshProductHistory();
  } catch (err) {
    showError(err.message);
  } finally {
    setLoading(false);
  }
});

// Filter & Search Event Listeners
filterSentimentGroup.addEventListener("click", (e) => {
  const btn = e.target.closest(".filter-btn");
  if (!btn) return;
  currentSentimentFilter = btn.dataset.filter;
  [...filterSentimentGroup.children].forEach(b => b.classList.toggle("active", b === btn));
  renderReviews();
});

filterPlatformGroup.addEventListener("click", (e) => {
  const btn = e.target.closest(".filter-btn");
  if (!btn) return;
  currentPlatformFilter = btn.dataset.platform;
  [...filterPlatformGroup.children].forEach(b => b.classList.toggle("active", b === btn));
  renderReviews();
});

reviewSearchInput.addEventListener("input", (e) => {
  currentSearchTerm = e.target.value.toLowerCase().trim();
  renderReviews();
});

// Export CSV Action
exportBtn.addEventListener("click", () => {
  if (currentProductId) {
    window.location.href = `${API_BASE}/api/export/${currentProductId}`;
  }
});

// Delete Product Action
deleteBtn.addEventListener("click", async () => {
  if (!currentProductId) return;
  if (confirm("Are you sure you want to delete this product analysis?")) {
    await fetch(`${API_BASE}/api/products/${currentProductId}`, { method: "DELETE" });
    currentProductId = null;
    dashboard.classList.add("hidden");
    exportBtn.classList.add("hidden");
    deleteBtn.classList.add("hidden");
    emptyState.classList.remove("hidden");
    await refreshProductHistory();
  }
});

// Dashboard Loader
async function loadDashboard(productId) {
  const [summaryRes, reviewsRes] = await Promise.all([
    fetch(`${API_BASE}/api/sentiment-summary/${productId}`),
    fetch(`${API_BASE}/api/reviews/${productId}`)
  ]);

  const summary = await summaryRes.json();
  const reviewsData = await reviewsRes.json();

  if (!summaryRes.ok) throw new Error(summary.error || "Could not load analytics summary.");
  if (!reviewsRes.ok) throw new Error(reviewsData.error || "Could not load reviews data.");

  currentReviews = reviewsData.reviews;
  currentProductId = productId;

  // Render Dashboard Views
  renderHeroCard(summary);
  renderPlatformComparison(summary.platform_breakdown);
  renderDistributionChart(summary.sentiment_counts);
  renderRatingsChart(summary.rating_distribution);
  renderProsAndCons(summary.pros_and_cons);
  renderWordChart(summary.word_frequency);
  renderTrendChart(summary.sentiment_trend);
  renderReviews();

  // Show UI Components
  emptyState.classList.add("hidden");
  dashboard.classList.remove("hidden");
  exportBtn.classList.remove("hidden");
  deleteBtn.classList.remove("hidden");
}

function renderHeroCard(summary) {
  const score = summary.satisfaction_score || 0;
  
  // Update Satisfaction Circular Gauge
  document.getElementById("hero-percent").textContent = `${score}%`;
  const gaugeFill = document.getElementById("gauge-fill");
  if (gaugeFill) {
    gaugeFill.setAttribute("stroke-dasharray", `${score}, 100`);
    if (score >= 70) gaugeFill.style.stroke = "#10B981";
    else if (score >= 45) gaugeFill.style.stroke = "#F59E0B";
    else gaugeFill.style.stroke = "#EF4444";
  }

  document.getElementById("hero-product-name").textContent = summary.product.name;
  document.getElementById("hero-collection-method").textContent = `Source: Amazon & Flipkart Live Scraping`;

  document.getElementById("stat-total").textContent = summary.total_reviews;
  document.getElementById("stat-rating").textContent = summary.average_rating ? `${summary.average_rating} ★` : "N/A";
  document.getElementById("stat-positive").textContent = summary.sentiment_counts.positive;
  document.getElementById("stat-negative").textContent = summary.sentiment_counts.negative;
}

function renderPlatformComparison(breakdown) {
  const amz = breakdown.Amazon || { count: 0, average_rating: null };
  const fk = breakdown.Flipkart || { count: 0, average_rating: null };

  document.getElementById("amazon-count").textContent = `${amz.count} reviews`;
  document.getElementById("amazon-rating").textContent = amz.average_rating ? `${amz.average_rating} / 5 ★` : "N/A";

  document.getElementById("flipkart-count").textContent = `${fk.count} reviews`;
  document.getElementById("flipkart-rating").textContent = fk.average_rating ? `${fk.average_rating} / 5 ★` : "N/A";
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
        backgroundColor: ["#10B981", "#F59E0B", "#EF4444"],
        borderWidth: 0
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "bottom",
          labels: { color: "#94A3B8", font: { family: "Inter", size: 12 }, boxWidth: 12 }
        }
      }
    }
  });
}

function renderRatingsChart(dist) {
  const ctx = document.getElementById("chart-ratings");
  destroyChart("ratings");

  charts.ratings = new Chart(ctx, {
    type: "bar",
    data: {
      labels: ["5 Stars ★", "4 Stars ★", "3 Stars ★", "2 Stars ★", "1 Star ★"],
      datasets: [{
        label: "Reviews",
        data: [dist[5] || 0, dist[4] || 0, dist[3] || 0, dist[2] || 0, dist[1] || 0],
        backgroundColor: ["#10B981", "#3B82F6", "#F59E0B", "#FB923C", "#EF4444"],
        borderRadius: 4
      }]
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: "#64748B", precision: 0 }, grid: { color: "rgba(255,255,255,0.05)" } },
        y: { ticks: { color: "#94A3B8" }, grid: { display: false } }
      }
    }
  });
}

function renderProsAndCons(prosCons) {
  const prosList = document.getElementById("pros-list");
  const consList = document.getElementById("cons-list");

  prosList.innerHTML = prosCons.pros.map(p => `<li><i class="fa-solid fa-check"></i> ${escapeHtml(p)}</li>`).join("");
  consList.innerHTML = prosCons.cons.map(c => `<li><i class="fa-solid fa-triangle-exclamation"></i> ${escapeHtml(c)}</li>`).join("");
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
        backgroundColor: "#06B6D4",
        borderRadius: 4
      }]
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: "#64748B", precision: 0 }, grid: { color: "rgba(255,255,255,0.05)" } },
        y: { ticks: { color: "#94A3B8" }, grid: { display: false } }
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
        { label: "Positive", data: trend.map(t => t.positive), borderColor: "#10B981", backgroundColor: "rgba(16, 185, 129, 0.1)", fill: true, tension: 0.3 },
        { label: "Neutral", data: trend.map(t => t.neutral), borderColor: "#F59E0B", backgroundColor: "rgba(245, 158, 11, 0.1)", fill: true, tension: 0.3 },
        { label: "Negative", data: trend.map(t => t.negative), borderColor: "#EF4444", backgroundColor: "rgba(239, 68, 68, 0.1)", fill: true, tension: 0.3 }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "bottom", labels: { color: "#94A3B8", font: { family: "Inter", size: 12 }, boxWidth: 10 } }
      },
      scales: {
        x: { ticks: { color: "#64748B", font: { size: 10 } }, grid: { display: false } },
        y: { beginAtZero: true, ticks: { color: "#64748B", precision: 0 }, grid: { color: "rgba(255,255,255,0.05)" } }
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
  reviewsList.innerHTML = "";

  let filtered = currentReviews;

  if (currentSentimentFilter !== "all") {
    filtered = filtered.filter(r => r.sentiment_label === currentSentimentFilter);
  }

  if (currentPlatformFilter !== "all") {
    filtered = filtered.filter(r => r.platform === currentPlatformFilter);
  }

  if (currentSearchTerm) {
    filtered = filtered.filter(r => 
      (r.review_text || "").toLowerCase().includes(currentSearchTerm) ||
      (r.review_title || "").toLowerCase().includes(currentSearchTerm)
    );
  }

  if (filtered.length === 0) {
    reviewsList.innerHTML = `<li class="review-card"><p class="review-body">No reviews match your selected filters.</p></li>`;
    return;
  }

  filtered.slice(0, 50).forEach(r => {
    const li = document.createElement("li");
    li.className = "review-card";
    
    const stars = r.rating ? "★".repeat(Math.round(r.rating)) + "☆".repeat(5 - Math.round(r.rating)) : "★ 4.0";
    const platformClass = r.platform || "Amazon";

    li.innerHTML = `
      <div class="review-card-header">
        <div class="review-badges">
          <span class="platform-pill ${platformClass}">${platformClass}</span>
          <span class="rating-stars">${stars} (${r.rating || 4.0})</span>
        </div>
        <span class="sentiment-badge ${r.sentiment_label}">${r.sentiment_label} (${r.sentiment_score})</span>
      </div>
      <div class="review-title">${escapeHtml(r.review_title || "Verified Customer Review")}</div>
      <div class="review-body">${escapeHtml(r.review_text)}</div>
      <div class="review-date"><i class="fa-regular fa-calendar"></i> ${r.review_date || "Recent"}</div>
    `;
    reviewsList.appendChild(li);
  });
}

async function refreshProductHistory() {
  try {
    const res = await fetch(`${API_BASE}/api/products`);
    const products = await res.json();

    productList.innerHTML = "";
    historyCount.textContent = products.length;

    products.forEach(p => {
      const li = document.createElement("li");
      li.className = "history-item";
      li.innerHTML = `
        <span class="history-item-name">${escapeHtml(p.name)}</span>
        <i class="fa-solid fa-chevron-right text-dim" style="font-size: 11px;"></i>
      `;
      li.addEventListener("click", () => loadDashboard(p.id));
      productList.appendChild(li);
    });
  } catch (err) {
    console.error("Could not refresh history:", err);
  }
}

function setLoading(isLoading, title = "Extracting Product Reviews...") {
  loadingState.classList.toggle("hidden", !isLoading);
  searchBtn.disabled = isLoading;
  searchBtn.innerHTML = isLoading 
    ? `<i class="fa-solid fa-spinner fa-spin"></i> Scraping...` 
    : `<i class="fa-solid fa-bolt"></i> Run Live Analysis`;
  
  if (isLoading) {
    document.getElementById("loading-title").textContent = title;
    emptyState.classList.add("hidden");
    dashboard.classList.add("hidden");
  }
}

function showError(msg) {
  errorBox.querySelector("#error-msg").textContent = msg;
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

// Initial Load
refreshProductHistory();
