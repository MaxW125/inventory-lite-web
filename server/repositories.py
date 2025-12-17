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

def create_sale_transaction(item_id, quantity, unit_price_at_time):
    """
    Record a sale transaction.
    Inventory updates are handled by the database trigger.
    """
    sql = """
        INSERT INTO transactions (
            item_id,
            type,
            quantity,
            unit_price_at_time
        )
        VALUES (%s, 'sale', %s, %s)
        RETURNING id;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql,
                (item_id, quantity, unit_price_at_time)
            )
            transaction_id = cur.fetchone()[0]
            conn.commit()

    return transaction_id

def create_restock_transaction(item_id, quantity, unit_price_at_time):
    """
    Record a restock transaction.
    Inventory updates are handled by the database trigger.
    """
    sql = """
        INSERT INTO transactions (
            item_id,
            type,
            quantity,
            unit_price_at_time
        )
        VALUES (%s, 'restock', %s, %s)
        RETURNING id;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql,
                (item_id, quantity, unit_price_at_time)
            )
            transaction_id = cur.fetchone()[0]
            conn.commit()

    return transaction_id

def get_low_stock_items(threshold):
    """
    Return items whose quantity_in_stock is below the given threshold.
    """
    sql = """
        SELECT
            id,
            sku,
            name,
            category,
            unit_price,
            quantity_in_stock
        FROM items
        WHERE quantity_in_stock < %s
        ORDER BY quantity_in_stock ASC;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (threshold,))
            rows = cur.fetchall()

    return rows

def get_sales_summary():
    """
    Return aggregated sales summary per item from the sales_summary view.
    """
    sql = """
        SELECT
            item_id,
            sku,
            name,
            units_sold,
            total_revenue
        FROM sales_summary
        ORDER BY total_revenue DESC;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()

    return rows