import sqlite3

db = sqlite3.connect("database.db")
c = db.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS cart (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    product_id INTEGER,
    quantity INTEGER
)
""")

db.commit()
db.close()

print("CART TABLE READY")
