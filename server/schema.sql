-- Drop tables if they already exist (safe for re-runs)
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS items;

-- Items table
CREATE TABLE items (
    id SERIAL PRIMARY KEY,
    sku TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    category TEXT,
    unit_price NUMERIC(10, 2) NOT NULL CHECK (unit_price >= 0),
    quantity_in_stock INTEGER NOT NULL CHECK (quantity_in_stock >= 0),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- Transactions table
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    item_id INTEGER NOT NULL REFERENCES items(id),
    type TEXT NOT NULL CHECK (type IN ('sale', 'restock')),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price_at_time NUMERIC(10, 2) NOT NULL CHECK (unit_price_at_time >= 0),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- Trigger function to update inventory after a transaction
CREATE OR REPLACE FUNCTION update_inventory_after_transaction()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.type = 'sale' THEN
        -- Prevent negative inventory
        IF (SELECT quantity_in_stock FROM items WHERE id = NEW.item_id) < NEW.quantity THEN
            RAISE EXCEPTION 'Not enough stock for item_id %', NEW.item_id;
        END IF;

        UPDATE items
        SET quantity_in_stock = quantity_in_stock - NEW.quantity
        WHERE id = NEW.item_id;

    ELSIF NEW.type = 'restock' THEN
        UPDATE items
        SET quantity_in_stock = quantity_in_stock + NEW.quantity
        WHERE id = NEW.item_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger
CREATE TRIGGER trg_update_inventory
AFTER INSERT ON transactions
FOR EACH ROW
EXECUTE FUNCTION update_inventory_after_transaction();

-- View: sales summary per item
CREATE OR REPLACE VIEW sales_summary AS
SELECT
    i.id AS item_id,
    i.sku,
    i.name,
    SUM(t.quantity) AS units_sold,
    SUM(t.quantity * t.unit_price_at_time) AS total_revenue
FROM items i
JOIN transactions t ON t.item_id = i.id
WHERE t.type = 'sale'
GROUP BY i.id, i.sku, i.name;