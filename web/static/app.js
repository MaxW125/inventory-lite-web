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
// Navigation (Products vs Materials)
// -----------------------------

function getActiveView() {
  const params = new URLSearchParams(window.location.search);
  const view = (params.get("view") || "products").toLowerCase();
  return view === "materials" ? "materials" : "products";
}

function applyViewVisibility() {
  const view = getActiveView();

  const productsPage = byId("productsPage");
  const materialsPage = byId("materialsPage");

  if (productsPage) productsPage.style.display = view === "products" ? "block" : "none";
  if (materialsPage) materialsPage.style.display = view === "materials" ? "block" : "none";

  const navProducts = byId("navProducts");
  const navMaterials = byId("navMaterials");

  if (navProducts) navProducts.classList.toggle("active", view === "products");
  if (navMaterials) navMaterials.classList.toggle("active", view === "materials");

  // Button label (Products page uses refreshBtn)
  const refreshBtn = byId("refreshBtn");
  if (refreshBtn) refreshBtn.textContent = view === "products" ? "Refresh Products" : "Refresh";
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

    const listed = !!p.is_listed;

    tr.innerHTML = `
      <td>${p.id ?? ""}</td>
      <td>${p.sku ?? ""}</td>
      <td>${p.name ?? ""}</td>
      <td>${p.price ?? ""}</td>
      <td>${p.unit_cost ?? "0"}</td>
      <td>
        <button
          type="button"
          class="secondary"
          data-listed-btn="${p.id}"
          data-listed="${listed}"
          title="Click to toggle"
        >
          ${listed ? "Yes" : "No"}
        </button>
      </td>
      <td>
        <button type="button" class="secondary" data-bom-btn="${p.id}">Recipe</button>
      </td>
    `;

    tbody.appendChild(tr);
  }

  // Wire Recipe buttons (event delegation) — attach once per page load
  if (!tbody.dataset.bomWired) {
    tbody.dataset.bomWired = "1";

    tbody.addEventListener("click", async (e) => {
      const listedBtn = e.target.closest("[data-listed-btn]");
      if (listedBtn) {
        const productId = parseInt(listedBtn.getAttribute("data-listed-btn"));
        const current = listedBtn.getAttribute("data-listed") === "true";
        const next = !current;

        const { res } = await setProductListed(productId, next);
        if (!res.ok) return alert("Failed to update listed status.");

        await loadProducts();
        return;
      }

      const btn = e.target.closest("[data-bom-btn]");
      if (!btn) return;

      const productId = parseInt(btn.getAttribute("data-bom-btn"));

      // toggle existing expanded row if present
      const existing = document.querySelector(`tr[data-bom-row="${productId}"]`);
      if (existing) {
        existing.remove();
        return;
      }

      // load data needed for UI
      const [bom, materials] = await Promise.all([
        loadBom(productId),
        (async () => {
          const { res, data } = await fetchJson("/api/materials");
          return res.ok ? data : [];
        })(),
      ]);

      // insert an expanded row directly after the product row
      const expandedTr = document.createElement("tr");
      expandedTr.setAttribute("data-bom-row", String(productId));

      const td = document.createElement("td");
      td.colSpan = 7; // ID, SKU, Name, Price, Unit Cost, Is Listed, Actions
      td.appendChild(renderBomRow({ productId, materials, bom }));

      expandedTr.appendChild(td);
      btn.closest("tr").after(expandedTr);

      // Remove handler (delegation inside expanded area)
      td.addEventListener("click", async (evt) => {
        // Add/Update (delegated so it still works after re-render)
        const add = evt.target.closest(`[data-bom-add="${productId}"]`);
        if (add) {
          const matSelect = td.querySelector(`[data-bom-material="${productId}"]`);
          const qtyInput = td.querySelector(`[data-bom-qty="${productId}"]`);

          const materialId = parseInt(matSelect.value);
          const qty = parseFloat(qtyInput.value || "0");

          const { res } = await upsertBomLine(productId, materialId, qty);
          if (!res.ok) return alert("Failed to save material line.");

          const newBom = await loadBom(productId);
          td.innerHTML = "";
          td.appendChild(renderBomRow({ productId, materials, bom: newBom }));

          // Refresh the computed unit cost in the Products table
          await refreshUnitCostForProduct(productId);
          return;
        }

        // Remove
        const rm = evt.target.closest("[data-bom-remove]");
        if (!rm) return;

        const [pid, mid] = rm.getAttribute("data-bom-remove").split(":").map(Number);

        const { res } = await deleteBomLine(pid, mid);
        if (!res.ok) return alert("Failed to remove line.");

        const newBom = await loadBom(pid);
        td.innerHTML = "";
        td.appendChild(renderBomRow({ productId: pid, materials, bom: newBom }));

        // Refresh the computed unit cost in the Products table
        await refreshUnitCostForProduct(pid);
      });
    });
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
      <td>${m.cost_per_unit ?? "0"}</td>
      <td>${m.brand ?? ""}</td>
      <td>${m.type ?? ""}</td>
      <td>${m.finish ?? ""}</td>
      <td>
        <button type="button" class="secondary" data-edit-material="${m.id}">Edit</button>
      </td>
    `;

    tbody.appendChild(tr);
  }
}

async function loadBom(productId) {
  const { res, data } = await fetchJson(`/api/products/${productId}/materials`);
  if (!res.ok) return [];

  return data;
}

async function upsertBomLine(productId, materialId, qtyPerUnit) {
  return fetchJson(`/api/products/${productId}/materials`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ material_id: materialId, qty_per_unit: qtyPerUnit }),
  });
}

async function deleteBomLine(productId, materialId) {
  return fetchJson(`/api/products/${productId}/materials/${materialId}`, {
    method: "DELETE",
  });
}

async function setProductListed(productId, isListed) {
  return fetchJson(`/api/products/${productId}/listed`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ is_listed: isListed }),
  });
}

async function refreshUnitCostForProduct(productId) {
  // Pull latest computed unit_cost from the backend and update the unit cost cell in-place
  const { res, data } = await fetchJson("/api/products");
  if (!res.ok || !Array.isArray(data)) return;

  const p = data.find((x) => Number(x.id) === Number(productId));
  if (!p) return;

  const productRowBtn = document.querySelector(`[data-bom-btn="${productId}"]`);
  const tr = productRowBtn?.closest("tr");
  if (!tr) return;

  // Column order: ID, SKU, Name, Price, Unit Cost, Is Listed, Actions
  const unitCostTd = tr.children?.[4];
  if (unitCostTd) unitCostTd.textContent = p.unit_cost ?? "0";
}

async function createMaterialFromForm(form) {
  const el = form.elements;

  const materialId = form.dataset.editingId
    ? parseInt(form.dataset.editingId)
    : (el["material_id"]?.value ? parseInt(el["material_id"].value) : null);

  const category = ((el["category"]?.value) || "OTHER").toUpperCase();

  const payload = {
    category,
    name: el["name"]?.value,                 // ✅ correct
    color: el["color"]?.value || "N/A",
    quantity_on_hand: el["quantity_on_hand"]?.value
      ? parseFloat(el["quantity_on_hand"].value)
      : 0,
    unit: el["unit"]?.value || (category === "FILAMENT" ? "g" : "pcs"),
    cost_per_unit: el["cost_per_unit"]?.value ? parseFloat(el["cost_per_unit"].value) : 0,
    brand: el["brand"]?.value || null,
    type: el["type"]?.value || null,
    finish: el["finish"]?.value || null,
  };

  const url = materialId ? `/api/materials/${materialId}` : "/api/materials";
  const method = materialId ? "PATCH" : "POST";

  const { res } = await fetchJson(url, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    alert("Error creating material. Check required fields.");
    return false;
  }

  // If we were editing, exit edit mode after a successful save
  if (materialId) {
    // Exit edit mode
    delete form.dataset.editingId;
    if (el["material_id"]) el["material_id"].value = "";
    const submitBtn = form.querySelector("button[type='submit']");
    if (submitBtn) submitBtn.textContent = "Add Material";
  }

  return true;
}

// -----------------------------
// Wiring
// -----------------------------

async function refreshAll() {
  const view = getActiveView();
  if (view === "products") {
    await loadProducts();
  } else {
    await loadMaterials();
  }
}

// Old refresh button still works
safeOn("refreshBtn", "click", refreshAll);
safeOn("refreshMaterialsBtn", "click", loadMaterials);

// Old form id still works: treat it as Add Product for V1
safeOn("addItemForm", "submit", async (e) => {
  e.preventDefault();
  const form = e.target;

  const ok = await createProductFromForm(form);
  if (!ok) return;

  form.reset();
  await loadProducts();
});

// New (optional) form id for materials if/when you add it in HTML
safeOn("addMaterialForm", "submit", async (e) => {
  e.preventDefault();
  const form = e.target;

  const ok = await createMaterialFromForm(form);
  if (!ok) return;

  form.reset();
  await loadMaterials();
});

safeOn("materialsTbody", "click", async (e) => {
  const btn = e.target.closest("[data-edit-material]");
  if (!btn) return;

  const id = parseInt(btn.getAttribute("data-edit-material"));

  const { res, data } = await fetchJson("/api/materials");
  if (!res.ok || !Array.isArray(data)) {
    alert("Failed to load materials for editing.");
    return;
  }

  const m = data.find((x) => Number(x.id) === Number(id));
  if (!m) {
    alert("Material not found.");
    return;
  }

  const form = byId("addMaterialForm");
  if (!form) return;

  // Enter edit mode (store id on form so submit PATCH is reliable)
  form.dataset.editingId = String(m.id);

  const el = form.elements;
  if (el["material_id"]) el["material_id"].value = m.id;

  if (el["category"]) el["category"].value = (m.category || "OTHER").toUpperCase();
  if (el["name"]) el["name"].value = m.name || "";
  if (el["color"]) el["color"].value = m.color || "N/A";
  if (el["quantity_on_hand"]) el["quantity_on_hand"].value = m.quantity_on_hand ?? 0;
  if (el["unit"]) el["unit"].value = m.unit || "";
  if (el["cost_per_unit"]) el["cost_per_unit"].value = m.cost_per_unit ?? 0;

  if (el["brand"]) el["brand"].value = m.brand || "";
  if (el["type"]) el["type"].value = m.type || "";
  if (el["finish"]) el["finish"].value = m.finish || "";

  const submitBtn = form.querySelector("button[type='submit']");
  if (submitBtn) submitBtn.textContent = "Save Changes";
  form.scrollIntoView({ behavior: "smooth", block: "start" });
});

// Load on page open
applyViewVisibility();
refreshAll();

function renderBomRow({ productId, materials, bom }) {
  const wrapper = document.createElement("div");
  wrapper.className = "bom";

  const options = materials.map(m => {
    const label = `${m.category} — ${m.name} (${m.color})`;
    return `<option value="${m.id}">${label}</option>`;
  }).join("");

  const bomLines = bom.map(line => {
    return `
      <tr>
        <td>${line.category}</td>
        <td>${line.name}</td>
        <td>${line.color}</td>
        <td>${line.qty_per_unit}</td>
        <td>${line.unit}</td>
        <td>
          <button type="button" class="secondary" data-bom-remove="${productId}:${line.material_id}">
            Remove
          </button>
        </td>
      </tr>
    `;
  }).join("");

  wrapper.innerHTML = `
    <div class="row" style="align-items: end;">
      <div class="field">
        <label>Add material</label>
        <select name="material_id" data-bom-material="${productId}">
          ${options}
        </select>
      </div>

      <div class="field" style="max-width: 180px;">
        <label>Qty per unit</label>
        <input type="number" step="0.01" name="qty_per_unit" placeholder="e.g. 35" data-bom-qty="${productId}" />
      </div>

      <button type="button" data-bom-add="${productId}">Add / Update</button>
    </div>

    <div style="height: 10px;"></div>

    <table border="1" cellpadding="6" cellspacing="0" style="width:100%;">
      <thead>
        <tr>
          <th>Category</th>
          <th>Name</th>
          <th>Color</th>
          <th>Qty/Unit</th>
          <th>Unit</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        ${bomLines || `<tr><td colspan="6" class="small">No materials yet.</td></tr>`}
      </tbody>
    </table>
  `;

  return wrapper;
}