from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
import json
from server.repositories import list_products, create_product, list_materials, create_material


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
        materials_input_raw = row[4]
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

    # Optional: list[dict]
    materials_used = payload.get("materials_used") or []

    product_id = create_product(
        sku=sku,
        name=name,
        price=price,
        materials_used=materials_used,
    )

    return {"id": product_id}


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
                "brand": row[6],
                "type": row[7],
                "finish": row[8],
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
        brand=payload.get("brand"),
        type=payload.get("type"),
        finish=payload.get("finish"),
    )

    return {"id": material_id}