from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
import json
from server.repositories import (
    list_products,
    create_product,
    set_product_listed,
    list_materials,
    create_material,
    update_material,
    list_product_materials,
    upsert_product_material,
    delete_product_material,
)


app = FastAPI()

# Static files (JS/CSS)
app.mount("/static", StaticFiles(directory="web/static"), name="static")

# Templates (HTML)
templates = Jinja2Templates(directory="web/templates")


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/products")
def get_products():
    rows = list_products()

    products = []
    for row in rows:
        # Expected row order: id, sku, name, price, is_listed, unit_cost, materials_input, created_at
        is_listed = row[4]
        unit_cost = row[5]
        materials_input_raw = row[6]
        materials_input = None
        if materials_input_raw:
            try:
                materials_input = json.loads(materials_input_raw)
            except Exception:
                # If older/bad data exists, return the raw string so UI still works.
                materials_input = materials_input_raw

        products.append(
            {
                "id": row[0],
                "sku": row[1],
                "name": row[2],
                "price": str(row[3]),
                "unit_cost": str(unit_cost),
                "is_listed": bool(is_listed),
                "materials_input": materials_input,
            }
        )

    return products


@app.post("/api/products")
def create_product_api(payload: dict):
    # Required
    sku = payload["sku"]
    name = payload["name"]
    price = payload["price"]
    is_listed = payload.get("is_listed", True)

    # Optional: list[dict]
    materials_used = payload.get("materials_used") or []

    product_id = create_product(
        sku=sku,
        name=name,
        price=price,
        is_listed=is_listed,
        materials_used=materials_used,
    )

    return {"id": product_id}

@app.patch("/api/products/{product_id}/listed")
def update_product_listed(product_id: int, payload: dict):
    is_listed = bool(payload["is_listed"])
    set_product_listed(product_id, is_listed)
    return {"ok": True}

@app.get("/api/materials")
def get_materials():
    rows = list_materials()

    materials = []
    for row in rows:
        materials.append(
            {
                "id": row[0],
                "name": row[1],
                "category": row[2],
                "color": row[3],
                "quantity_on_hand": row[4],
                "unit": row[5],
                "cost_per_unit": str(row[6]),
                "brand": row[7],
                "type": row[8],
                "finish": row[9],
            }
        )

    return materials


@app.post("/api/materials")
def create_material_api(payload: dict):
    material_id = create_material(
        name=payload["name"],
        category=(payload.get("category") or "OTHER").upper(),
        color=payload.get("color") or "N/A",
        quantity_on_hand=payload.get("quantity_on_hand", 0),
        unit=payload.get("unit") or ("g" if (payload.get("category") or "").upper() == "FILAMENT" else "pcs"),
        cost_per_unit=payload.get("cost_per_unit", 0),
        brand=payload.get("brand"),
        type=payload.get("type"),
        finish=payload.get("finish"),
    )

    return {"id": material_id}

@app.patch("/api/materials/{material_id}")
def update_material_api(material_id: int, payload: dict):
    update_material(
        material_id=material_id,
        category=(payload.get("category") or "OTHER").upper(),
        name=payload.get("name"),
        color=payload.get("color") or "N/A",
        quantity_on_hand=payload.get("quantity_on_hand", 0),
        unit=payload.get("unit") or ("g" if (payload.get("category") or "").upper() == "FILAMENT" else "pcs"),
        cost_per_unit=payload.get("cost_per_unit", 0),
        brand=payload.get("brand"),
        type=payload.get("type"),
        finish=payload.get("finish"),
    )

    return {"ok": True}

@app.get("/api/products/{product_id}/materials")
def get_product_bom(product_id: int):
    rows = list_product_materials(product_id)

    bom = []
    for row in rows:
        bom.append({
            "material_id": row[0],
            "category": row[1],
            "name": row[2],
            "color": row[3],
            "unit": row[4],
            "qty_per_unit": str(row[5]),
        })

    return bom


@app.post("/api/products/{product_id}/materials")
def upsert_product_bom_line(product_id: int, payload: dict):
    # required
    material_id = int(payload["material_id"])
    qty_per_unit = payload.get("qty_per_unit", 0)

    upsert_product_material(product_id, material_id, qty_per_unit)
    return {"ok": True}


@app.delete("/api/products/{product_id}/materials/{material_id}")
def delete_product_bom_line(product_id: int, material_id: int):
    delete_product_material(product_id, material_id)
    return {"ok": True}