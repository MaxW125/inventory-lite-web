from server.db import get_connection


def list_items():
    """
    Return all items in the inventory.
    """
    sql = """
        SELECT
            id,
            sku,
            name,
            category,
            unit_price,
            quantity_in_stock,
            created_at
        FROM items
        ORDER BY id;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()

    return rows

def create_item(sku, name, category, unit_price, quantity_in_stock):
    """
    Insert a new item into the inventory.
    """
    sql = """
        INSERT INTO items (
            sku,
            name,
            category,
            unit_price,
            quantity_in_stock
        )
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql,
                (sku, name, category, unit_price, quantity_in_stock)
            )
            item_id = cur.fetchone()[0]
            conn.commit()

    return item_id