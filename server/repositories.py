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
            cost_per_unit,
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
    cost_per_unit=0,
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
            cost_per_unit,
            brand,
            type,
            finish
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql,
                (name, category, color, quantity_on_hand, unit, cost_per_unit, brand, type, finish),
            )
            material_id = cur.fetchone()[0]
            conn.commit()

    return material_id


def update_material(
    material_id: int,
    category,
    name,
    color,
    quantity_on_hand,
    unit,
    cost_per_unit,
    brand=None,
    type=None,
    finish=None,
):
    """Update an existing material row."""
    sql = """
        UPDATE materials
        SET
            category = %s,
            name = %s,
            color = %s,
            quantity_on_hand = %s,
            unit = %s,
            cost_per_unit = %s,
            brand = %s,
            type = %s,
            finish = %s
        WHERE id = %s;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql,
                (
                    category,
                    name,
                    color,
                    quantity_on_hand,
                    unit,
                    cost_per_unit,
                    brand,
                    type,
                    finish,
                    material_id,
                ),
            )
            conn.commit()


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
                cost_per_unit,
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
                cost_per_unit,
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
      - optional: quantity_on_hand, unit, cost_per_unit
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
    cost_per_unit = material.get("cost_per_unit", 0)

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
        cost_per_unit=cost_per_unit,
        brand=brand if category == "FILAMENT" else None,
        type=mtype if category == "FILAMENT" else None,
        finish=finish if category == "FILAMENT" else None,
    )


# -----------------------------
# Products
# -----------------------------

def list_products():
    """Return all products (including live unit_cost computed from BOM)."""
    sql = """
        SELECT
            p.id,
            p.sku,
            p.name,
            p.price,
            p.is_listed,
            COALESCE(SUM(pm.qty_per_unit * m.cost_per_unit), 0) AS unit_cost,
            p.materials_input
        FROM products p
        LEFT JOIN product_materials pm ON pm.product_id = p.id
        LEFT JOIN materials m ON m.id = pm.material_id
        GROUP BY
            p.id,
            p.sku,
            p.name,
            p.price,
            p.is_listed,
            p.materials_input
        ORDER BY p.id;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()

    return rows


def create_product(sku, name, price, materials_used=None, is_listed=True):
    """Create a product.

    - Inserts a product row (sku, name, price, is_listed)
    - If materials_used is provided (list of dicts), the function will:
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
            is_listed,
            materials_input
        )
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (sku, name, price, is_listed, materials_input))
            product_id = cur.fetchone()[0]
            conn.commit()

    return product_id


def set_product_listed(product_id: int, is_listed: bool):
    """Update whether a product is actively listed/sellable."""
    sql = """
        UPDATE products
        SET is_listed = %s
        WHERE id = %s;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (is_listed, product_id))
            conn.commit()


# -----------------------------
# Product BOM (recipe)
# -----------------------------

def list_product_materials(product_id: int):
    """Return the BOM (recipe) for a product."""
    sql = """
        SELECT
            pm.material_id,
            m.category,
            m.name,
            m.color,
            m.unit,
            pm.qty_per_unit
        FROM product_materials pm
        JOIN materials m ON m.id = pm.material_id
        WHERE pm.product_id = %s
        ORDER BY m.category, m.name, m.color;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (product_id,))
            return cur.fetchall()


def upsert_product_material(product_id: int, material_id: int, qty_per_unit):
    """Add or update one material line on a product BOM."""
    sql = """
        INSERT INTO product_materials (product_id, material_id, qty_per_unit)
        VALUES (%s, %s, %s)
        ON CONFLICT (product_id, material_id)
        DO UPDATE SET qty_per_unit = EXCLUDED.qty_per_unit;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (product_id, material_id, qty_per_unit))
            conn.commit()


def delete_product_material(product_id: int, material_id: int):
    """Remove one material line from a product BOM."""
    sql = """
        DELETE FROM product_materials
        WHERE product_id = %s AND material_id = %s;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (product_id, material_id))
            conn.commit()
