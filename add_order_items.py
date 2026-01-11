import sqlite3

con = sqlite3.connect("database.db")
cur = con.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER,
    product_name TEXT,
    price REAL,
    quantity INTEGER
)
""")

con.commit()
con.close()

print("ORDER ITEMS TABLE READY")
