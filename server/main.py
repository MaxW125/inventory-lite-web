from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from server.repositories import list_items, create_item, create_sale_transaction, create_restock_transaction, get_low_stock_items, get_sales_summary


app = FastAPI()

# Static files (JS/CSS)
app.mount("/static", StaticFiles(directory="web/static"), name="static")

# Templates (HTML)
templates = Jinja2Templates(directory="web/templates")


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/items")
def get_items():
    rows = list_items()

    items = []
    for row in rows:
        items.append({
            "id": row[0],
            "sku": row[1],
            "name": row[2],
            "category": row[3],
            "unit_price": str(row[4]),
            "quantity_in_stock": row[5],
            "created_at": row[6].isoformat(),
        })

    return items

@app.post("/api/items")
def create_item_api(payload: dict):
    item_id = create_item(
        sku=payload["sku"],
        name=payload["name"],
        category=payload.get("category"),
        unit_price=payload["unit_price"],
        quantity_in_stock=payload["quantity_in_stock"],
    )

    return {"id": item_id}

@app.post("/api/transactions/sale")
def create_sale(payload: dict):
    tx_id = create_sale_transaction(
        item_id=payload["item_id"],
        quantity=payload["quantity"],
        unit_price_at_time=payload["unit_price_at_time"],
    )

    return {"transaction_id": tx_id}

@app.post("/api/transactions/restock")
def create_restock(payload: dict):
    tx_id = create_restock_transaction(
        item_id=payload["item_id"],
        quantity=payload["quantity"],
        unit_price_at_time=payload["unit_price_at_time"],
    )

    return {"transaction_id": tx_id}

@app.get("/api/reports/low-stock")
def low_stock_report(threshold: int = 5):
    rows = get_low_stock_items(threshold)

    report = []
    for row in rows:
        report.append({
            "id": row[0],
            "sku": row[1],
            "name": row[2],
            "category": row[3],
            "unit_price": str(row[4]),
            "quantity_in_stock": row[5],
        })

    return report

@app.get("/api/reports/sales-summary")
def sales_summary_report():
    rows = get_sales_summary()

    report = []
    for row in rows:
        report.append({
            "item_id": row[0],
            "sku": row[1],
            "name": row[2],
            "units_sold": row[3],
            "total_revenue": str(row[4]),
        })

    return report