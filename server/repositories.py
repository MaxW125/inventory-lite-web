from server.db import get_connection
import json


# -----------------------------
# Materials
# -----------------------------

def list_materials():
    """Return all materials (filament + other supplies)."""
    sql = """
        SELECT
            id,
            name,
            category,
            color,
            quantity_on_hand,
            unit,
            brand,
            type,
            finish
        FROM materials
        ORDER BY id;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()

    return rows


def create_material(
    name,
    category,
    color,
    quantity_on_hand=0,
    unit="pcs",
    brand=None,
    type=None,
    finish=None,
):
    """Insert a new material. Returns the new material id."""
    sql = """
        INSERT INTO materials (
            name,
            category,
            color,
            quantity_on_hand,
            unit,
            brand,
            type,
            finish
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql,
                (name, category, color, quantity_on_hand, unit, brand, type, finish),
            )
            material_id = cur.fetchone()[0]
            conn.commit()

    return material_id


def find_material(category, name, color, brand=None, type=None, finish=None):
    """Find a material by its identity fields. Returns the row or None."""
    # Identity rule for V1:
    # - FILAMENT: match category+name+color+brand+type+finish
    # - Non-filament: match category+name+color (brand/type/finish ignored)
    if (category or "").upper() == "FILAMENT":
        sql = """
            SELECT
                id,
                name,
                category,
                color,
                quantity_on_hand,
                unit,
                brand,
                type,
                finish
            FROM materials
            WHERE category = %s
              AND name = %s
              AND color = %s
              AND COALESCE(brand, '') = COALESCE(%s, '')
              AND COALESCE(type, '') = COALESCE(%s, '')
              AND COALESCE(finish, '') = COALESCE(%s, '')
            LIMIT 1;
        """
        params = (category, name, color, brand, type, finish)
    else:
        sql = """
            SELECT
                id,
                name,
                category,
                color,
                quantity_on_hand,
                unit,
                brand,
                type,
                finish
            FROM materials
            WHERE category = %s
              AND name = %s
              AND color = %s
            LIMIT 1;
        """
        params = (category, name, color)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()

    return row


def find_or_create_material(material):
    """Upsert-like helper used during product creation.

    Expects a dict with keys:
      - category, name, color
      - optional: quantity_on_hand, unit
      - filament optional: brand, type, finish

    Returns: material_id
    """
    category = (material.get("category") or "OTHER").strip().upper()
    name = (material.get("name") or "").strip()
    color = (material.get("color") or "N/A").strip()

    if not name:
        raise ValueError("Material name is required")

    brand = (material.get("brand") or None)
    mtype = (material.get("type") or None)
    finish = (material.get("finish") or None)

    # Defaults
    quantity_on_hand = material.get("quantity_on_hand", 0)
    unit = material.get("unit")
    if not unit:
        unit = "g" if category == "FILAMENT" else "pcs"

    existing = find_material(
        category=category,
        name=name,
        color=color,
        brand=brand,
        type=mtype,
        finish=finish,
    )
    if existing:
        return existing[0]

    return create_material(
        name=name,
        category=category,
        color=color,
        quantity_on_hand=quantity_on_hand,
        unit=unit,
        brand=brand if category == "FILAMENT" else None,
        type=mtype if category == "FILAMENT" else None,
        finish=finish if category == "FILAMENT" else None,
    )


# -----------------------------
# Products
# -----------------------------

def list_products():
    """Return all products."""
    sql = """
        SELECT
            id,
            sku,
            name,
            price,
            materials_input
        FROM products
        ORDER BY id;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()

    return rows


def create_product(sku, name, price, materials_used=None):
    """Create a product.

    If materials_used is provided (list of dicts), the function will:
      1) ensure each material exists (auto-add into materials table)
      2) store the original list into products.materials_input (JSON text)

    Returns: product_id
    """
    materials_used = materials_used or []

    # Auto-add materials first (so product create fails early if invalid material entries)
    for m in materials_used:
        find_or_create_material(m)

    materials_input = json.dumps(materials_used)

    sql = """
        INSERT INTO products (
            sku,
            name,
            price,
            materials_input
        )
        VALUES (%s, %s, %s, %s)
        RETURNING id;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (sku, name, price, materials_input))
            product_id = cur.fetchone()[0]
            conn.commit()

    return product_id