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

// -----------------------------
// Helpers
// -----------------------------

function byId(id) {
  return document.getElementById(id);
}

function safeOn(id, eventName, handler) {
  const el = byId(id);
  if (!el) return;
  el.addEventListener(eventName, handler);
}

async function fetchJson(url, options) {
  const res = await fetch(url, options);
  const data = await res.json().catch(() => null);
  return { res, data };
}

// -----------------------------
// Products
// -----------------------------

async function loadProducts() {
  // New V1 endpoint
  const { res, data } = await fetchJson("/api/products");
  if (!res.ok) {
    console.error("❌ Failed to load products", data);
    return;
  }

  // Prefer a dedicated products tbody if you add one later.
  // Fallback to the old itemsTbody so the existing page still renders something.
  const tbody = byId("productsTbody") || byId("itemsTbody");
  if (!tbody) return;

  tbody.innerHTML = "";

  for (const p of data) {
    const tr = document.createElement("tr");

    tr.innerHTML = `
      <td>${p.id ?? ""}</td>
      <td>${p.sku ?? ""}</td>
      <td>${p.name ?? ""}</td>
      <td>${p.price ?? ""}</td>
    `;

    tbody.appendChild(tr);
  }
}

async function createProductFromForm(form) {
  const el = form.elements;

  const payload = {
    sku: el["sku"]?.value,
    name: el["name"]?.value, // ✅ correct
    price: el["price"]
      ? parseFloat(el["price"].value)
      : parseFloat(el["unit_price"]?.value),
    materials_used: [],
  };

  const { res } = await fetchJson("/api/products", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    alert("Error creating product (check SKU uniqueness and price).");
    return false;
  }

  return true;
}

// -----------------------------
// Materials
// -----------------------------

async function loadMaterials() {
  const { res, data } = await fetchJson("/api/materials");
  if (!res.ok) {
    console.error("❌ Failed to load materials", data);
    return;
  }

  const tbody = byId("materialsTbody");
  if (!tbody) return; // Only renders if your HTML includes this table.

  tbody.innerHTML = "";

  for (const m of data) {
    const tr = document.createElement("tr");

    tr.innerHTML = `
      <td>${m.id ?? ""}</td>
      <td>${m.category ?? ""}</td>
      <td>${m.name ?? ""}</td>
      <td>${m.color ?? ""}</td>
      <td>${m.quantity_on_hand ?? 0}</td>
      <td>${m.unit ?? ""}</td>
      <td>${m.brand ?? ""}</td>
      <td>${m.type ?? ""}</td>
      <td>${m.finish ?? ""}</td>
    `;

    tbody.appendChild(tr);
  }
}

async function createMaterialFromForm(form) {
  const el = form.elements;

  const category = ((el["category"]?.value) || "OTHER").toUpperCase();

  const payload = {
    category,
    name: el["name"]?.value,                 // ✅ correct
    color: el["color"]?.value || "N/A",
    quantity_on_hand: el["quantity_on_hand"]?.value
      ? parseFloat(el["quantity_on_hand"].value)
      : 0,
    unit: el["unit"]?.value || (category === "FILAMENT" ? "g" : "pcs"),
    brand: el["brand"]?.value || null,
    type: el["type"]?.value || null,
    finish: el["finish"]?.value || null,
  };

  const { res } = await fetchJson("/api/materials", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    alert("Error creating material. Check required fields.");
    return false;
  }

  return true;
}

// -----------------------------
// Wiring
// -----------------------------

async function refreshAll() {
  await Promise.all([loadProducts(), loadMaterials()]);
}

// Old refresh button still works
safeOn("refreshBtn", "click", refreshAll);

// Old form id still works: treat it as Add Product for V1
safeOn("addItemForm", "submit", async (e) => {
  e.preventDefault();
  const form = e.target;

  const ok = await createProductFromForm(form);
  if (!ok) return;

  form.reset();
  await refreshAll();
});

// New (optional) form id for materials if/when you add it in HTML
safeOn("addMaterialForm", "submit", async (e) => {
  e.preventDefault();
  const form = e.target;

  const ok = await createMaterialFromForm(form);
  if (!ok) return;

  form.reset();
  await refreshAll();
});

// Load on page open
refreshAll();