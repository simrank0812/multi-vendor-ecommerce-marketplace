const csrf = () => document.querySelector('meta[name="csrf"]').content;

function toast(text, type = "info") {
  let box = document.querySelector(".msgs");
  if (!box) { box = document.createElement("div"); box.className = "msgs"; document.body.appendChild(box); }
  const m = document.createElement("div");
  m.className = "msg " + type; m.textContent = text; box.appendChild(m);
  setTimeout(() => m.remove(), 3500);
}

async function postJSON(url, data) {
  const res = await fetch(url, {
    method: "POST", headers: {"Content-Type": "application/json", "X-CSRFToken": csrf()},
    body: JSON.stringify(data),
  });
  return {status: res.status, data: await res.json()};
}

function setCount(n) {
  const el = document.getElementById("cart-count");
  if (el) { el.textContent = n; el.style.display = n ? "inline-block" : "none"; }
}

// Add to cart (AJAX) ------------------------------------------------
document.addEventListener("click", async (e) => {
  const btn = e.target.closest(".add-to-cart");
  if (!btn) return;
  const qtyInput = document.getElementById("detail-qty");
  const {status, data} = await postJSON(btn.dataset.url, {
    product_id: btn.dataset.id, quantity: qtyInput ? qtyInput.value : 1});
  if (data.login) { window.location = btn.dataset.login; return; }
  toast(data.message, data.ok ? "success" : "error");
  if (data.ok) setCount(data.count);
});

// Cart page: + / - / remove ---------------------------------------------
document.addEventListener("click", async (e) => {
  const btn = e.target.closest(".qty-btn");
  if (!btn) return;
  const row = btn.closest("tr");
  const current = parseInt(row.querySelector(".qty-val").textContent);
  const next = btn.dataset.action === "inc" ? current + 1 : btn.dataset.action === "dec" ? current - 1 : 0;
  const {data} = await postJSON(btn.dataset.url, {item_id: row.dataset.item, quantity: next});
  if (!data.ok) { toast(data.message, "error"); return; }
  if (data.removed) row.remove(); else {
    row.querySelector(".qty-val").textContent = next;
    row.querySelector(".line-total").textContent = data.line_total;
  }
  document.getElementById("cart-total").textContent = data.total;
  setCount(data.count);
  if (data.count === 0) location.reload();
});

// Auto-submit filter form with debounce -------------------------------------
const filterForm = document.getElementById("filter-form");
if (filterForm) {
  let t;
  filterForm.addEventListener("input", (e) => {
    clearTimeout(t);
    t = setTimeout(() => filterForm.submit(), e.target.type === "select-one" ? 0 : 600);
  });
}

// Auto-hide Django messages ----------------------------------------------
document.querySelectorAll(".msg").forEach((m) => setTimeout(() => m.remove(), 4000));

// Seller sales bar chart ------------------------------------------------
const chartData = document.getElementById("chart-data");
if (chartData) {
  const rows = JSON.parse(chartData.textContent);
  const max = Math.max(...rows.map((r) => r.value), 1);
  const box = document.getElementById("chart");
  rows.forEach((r) => {
    const col = document.createElement("div"); col.className = "bar";
    col.innerHTML = `<b>${r.value ? "₹" + r.value.toFixed(0) : ""}</b><div style="height:0"></div><small>${r.label}</small>`;
    box.appendChild(col);
    requestAnimationFrame(() => setTimeout(() => (col.querySelector("div").style.height = (r.value / max) * 85 + "%"), 50));
  });
}

// Confirm dialogs -------------------------------------------------------
document.addEventListener("submit", (e) => {
  const msg = e.target.dataset.confirm;
  if (msg && !confirm(msg)) e.preventDefault();
});
