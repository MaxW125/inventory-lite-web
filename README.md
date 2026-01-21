# Mountory Inventory

Mountory Inventory is a purpose-built full-stack inventory system for managing products and materials for my 3D printing shop (**Mountory**).

The project intentionally uses a **minimal, transparent tech stack** to demonstrate backend fundamentals, data modeling, and clean API design without hiding logic behind heavy frameworks or ORMs. What started as a generic inventory demo was deliberately pivoted into a real operational tool used to track filament, hardware, and sellable products.

---

## 🚀 Features (V1)

### Products
- Create products with:
  - SKU
  - Name
  - Price
- View all products in a live table

### Materials
- Track materials including:
  - Filament (brand, color, type, finish, quantity)
  - Hardware (screws, magnets, etc.)
  - Packaging and miscellaneous supplies
- Quantity on hand tracking
- Supports different units (grams, pieces, etc.)

### System
- PostgreSQL-backed persistence
- Clean repository layer using raw SQL
- REST API via FastAPI
- Lightweight frontend using vanilla JavaScript

---

## 🧰 Tech Stack

### Backend
- Python
- FastAPI
- psycopg (raw SQL, no ORM)

### Frontend
- HTML
- CSS
- Vanilla JavaScript (`fetch` API)

### Database
- PostgreSQL
- Handwritten SQL schema
- Explicit constraints and indexes

---

## 🏗 Architecture Overview

- **PostgreSQL** stores all application data
- **Raw SQL repositories** isolate all database access
- **FastAPI** exposes REST endpoints and serves the frontend
- **Vanilla JS frontend** communicates with the API using `fetch()`

The system is intentionally simple, readable, and easy to extend.

---

## 📁 Project Structure

```text
mountory-inventory/
  server/
    main.py            # FastAPI app and routes
    db.py              # PostgreSQL connection helpers
    repositories.py    # Raw SQL queries
    schema.sql         # Database schema
  web/
    templates/
      index.html       # Main UI
    static/
      app.js           # Frontend logic
      styles.css       # Styling
  docker-compose.yml  # PostgreSQL container
  requirements.txt
  README.md
```

---

## ⚙️ Getting Started

### Prerequisites
- Python 3.11+
- Docker
- Git

---

### Setup

Clone the repository:

```bash
git clone https://github.com/MaxW125/mountory-inventory.git
cd mountory-inventory
```

Start PostgreSQL:

```bash
docker compose up -d
```

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the server:

```bash
python -m uvicorn server.main:app --reload
```

Open in browser:

```
http://127.0.0.1:8000/
```

---

## 🔌 API Endpoints (V1)

### Products
- `GET /api/products`
- `POST /api/products`

### Materials
- `GET /api/materials`
- `POST /api/materials`

---

## 🧭 Design Philosophy

This project emphasizes:

- Minimal dependencies
- Explicit SQL over ORMs
- Clear separation of concerns
- Predictable data flow
- Production-minded schema design

The goal is correctness, clarity, and extensibility over abstraction.

---

## 🗺 Roadmap (Planned)

- Attach materials directly to products (join table)
- Automatically deduct material inventory when products are sold
- Cost calculation per product
- Profit tracking
- Low-stock alerts and reorder thresholds
- Simple authentication
- Deployment pipeline

---

## 📜 License

This project is intended for educational and portfolio purposes.