# Inventory Lite

Inventory Lite is a simple full-stack web application for managing a hypothetical business’s inventory.

The project is intentionally built with a **minimal, transparent tech stack** to demonstrate core backend and full-stack fundamentals without hiding logic behind heavy frameworks or ORMs.

---

## Features

- Create inventory items (SKU, name, category, unit price, quantity)
- Record sales and restocks
- Automatic inventory updates using database triggers
- Low-stock reporting
- Sales summary reporting (units sold and total revenue per item)

---

## Tech Stack

### Backend
- Python
- FastAPI
- psycopg (raw SQL, no ORM)

### Frontend
- HTML
- CSS
- Vanilla JavaScript (`fetch` API)

### Database
- PostgreSQL (Dockerized)
- Raw SQL schema
- Primary keys, foreign keys, and constraints
- Triggers for inventory updates
- Views for aggregated reporting

---

## Architecture Overview

- **PostgreSQL** stores all application data and enforces business rules
- **Database triggers** automatically update inventory after transactions
- **Database views** handle reporting logic
- **FastAPI** exposes a REST API and serves the frontend
- **Repository layer** contains all raw SQL queries
- **Vanilla JavaScript frontend** communicates with the API using `fetch()`

Inventory changes are recorded as immutable **transactions**, ensuring a clear audit trail.

---

## Project Structure

```text
inventory-lite-web/
  server/
    main.py            # FastAPI app and routes
    db.py              # PostgreSQL connection helpers
    repositories.py    # Raw SQL queries
    schema.sql         # Tables, triggers, and views
  web/
    templates/
      index.html       # Main UI
    static/
      app.js           # Frontend logic
      styles.css       # Minimal styling
  docker-compose.yml  # PostgreSQL container
  requirements.txt
  README.md
```

---

## Getting Started

These instructions will get the project running locally.

### Prerequisites
- Docker
- Python 3.11+
- Git

---

### Setup

Clone the repository:

```bash
git clone https://github.com/MaxW125/inventory-lite-web.git
cd inventory-lite-web
```

Start PostgreSQL using Docker:

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

Run the FastAPI server:

```bash
uvicorn server.main:app --reload
```

Open the application in your browser:

```
http://127.0.0.1:8000/
```

---

## Resetting the Database (Local Development)

To reset the database to a clean state during local development:

1) Stop FastAPI (if running)

```
Ctrl + C
```

2) Stop Postgres and delete the data volume 

```bash
docker compose down -v
```

3) Start Postgres again (empty)

```bash
docker compose up -d
```

4) Re-create the schema

```bash
docker compose exec -T postgres psql -U inventory_user -d inventory_db < server/schema.sql
```

5) Start FastAPI again

```bash
uvicorn server.main:app --reload
```

---

## API Endpoints

### Items
- `GET /api/items`
- `POST /api/items`

### Transactions
- `POST /api/transactions/sale`
- `POST /api/transactions/restock`

### Reports
- `GET /api/reports/low-stock`
- `GET /api/reports/sales-summary`

---

## Design Philosophy

This project emphasizes:

- Minimal dependencies
- Clear separation of concerns
- Explicit SQL instead of ORMs
- Database-level data integrity (constraints, triggers, and views)

The focus is correctness, clarity, and real-world fundamentals over abstraction.

---

## Future Improvements

- Request validation with Pydantic
- Improved error handling
- Authentication and authorization
- UI polish
- Pagination and filtering
- Deployment configuration

---

## License

This project is intended for educational and portfolio purposes.