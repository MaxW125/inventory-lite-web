import psycopg


DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "inventory_db",
    "user": "inventory_user",
    "password": "inventory_password",
}


def get_connection():
    """
    Create and return a new database connection.
    Caller is responsible for closing it.
    """
    return psycopg.connect(**DB_CONFIG)