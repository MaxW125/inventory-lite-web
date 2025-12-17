// Theme toggle (dark/light) with persistence
(function initTheme() {
  const saved = localStorage.getItem("theme");
  if (saved === "light") {
    document.documentElement.setAttribute("data-theme", "light");
  }
})();

function updateThemeToggleLabel() {
  const btn = document.getElementById("themeToggle");
  if (!btn) return;
  const isLight = document.documentElement.getAttribute("data-theme") === "light";
  btn.textContent = isLight ? "Dark mode" : "Light mode";
}

(function setupThemeToggle() {
  const btn = document.getElementById("themeToggle");
  if (!btn) return;

  updateThemeToggleLabel();

  btn.addEventListener("click", () => {
    const isLight = document.documentElement.getAttribute("data-theme") === "light";

    if (isLight) {
      document.documentElement.removeAttribute("data-theme");
      localStorage.removeItem("theme");
    } else {
      document.documentElement.setAttribute("data-theme", "light");
      localStorage.setItem("theme", "light");
    }

    updateThemeToggleLabel();
  });
})();

async function loadItems() {
  const res = await fetch("/api/items");
  const items = await res.json();

  const tbody = document.getElementById("itemsTbody");
  tbody.innerHTML = "";

  for (const item of items) {
    const tr = document.createElement("tr");

    tr.innerHTML = `
      <td>${item.id}</td>
      <td>${item.sku}</td>
      <td>${item.name}</td>
      <td>${item.category ?? ""}</td>
      <td>${item.unit_price}</td>
      <td>${item.quantity_in_stock}</td>
      <td>${item.created_at}</td>
    `;

    tbody.appendChild(tr);
  }
}

document.getElementById("refreshBtn").addEventListener("click", loadItems);

// Load on page open
loadItems();

document
  .getElementById("addItemForm")
  .addEventListener("submit", async (e) => {
    e.preventDefault();

    const form = e.target;

    const payload = {
      sku: form.sku.value,
      name: form.name.value,
      category: form.category.value || null,
      unit_price: parseFloat(form.unit_price.value),
      quantity_in_stock: parseInt(form.quantity_in_stock.value),
    };

    const res = await fetch("/api/items", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      alert("Error creating item (check SKU uniqueness)");
      return;
    }

    form.reset();
    loadItems();
  });

  document.getElementById("saleForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.target;

  const payload = {
    item_id: parseInt(form.item_id.value),
    quantity: parseInt(form.quantity.value),
    unit_price_at_time: parseFloat(form.unit_price_at_time.value),
  };

  const res = await fetch("/api/transactions/sale", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    alert("Sale failed (possible not enough stock).");
    return;
  }

  form.reset();
  loadItems();
});

document.getElementById("restockForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.target;

  const payload = {
    item_id: parseInt(form.item_id.value),
    quantity: parseInt(form.quantity.value),
    unit_price_at_time: parseFloat(form.unit_price_at_time.value),
  };

  const res = await fetch("/api/transactions/restock", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    alert("Restock failed.");
    return;
  }

  form.reset();
  loadItems();
});

async function loadLowStock() {
  const res = await fetch("/api/reports/low-stock");
  const items = await res.json();

  const tbody = document.getElementById("lowStockTbody");
  tbody.innerHTML = "";

  for (const item of items) {
    const tr = document.createElement("tr");

    tr.innerHTML = `
      <td>${item.id}</td>
      <td>${item.sku}</td>
      <td>${item.name}</td>
      <td>${item.quantity_in_stock}</td>
    `;

    tbody.appendChild(tr);
  }
}

document
  .getElementById("loadLowStockBtn")
  .addEventListener("click", loadLowStock);

  async function loadSalesSummary() {
  const res = await fetch("/api/reports/sales-summary");
  const rows = await res.json();

  const tbody = document.getElementById("salesSummaryTbody");
  tbody.innerHTML = "";

  for (const r of rows) {
    const tr = document.createElement("tr");

    tr.innerHTML = `
      <td>${r.item_id}</td>
      <td>${r.sku}</td>
      <td>${r.name}</td>
      <td>${r.units_sold}</td>
      <td>${r.total_revenue}</td>
    `;

    tbody.appendChild(tr);
  }
}

document
  .getElementById("loadSalesSummaryBtn")
  .addEventListener("click", loadSalesSummary);