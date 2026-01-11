import sqlite3

db = sqlite3.connect("database.db")
c = db.cursor()

c.execute("""
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    email TEXT UNIQUE,
    password TEXT,
    is_admin INTEGER DEFAULT 0
)
""")

c.execute("""
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE
)
""")

c.execute("""
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    price REAL,
    image TEXT,
    category_id INTEGER
)
""")

c.execute("""
INSERT INTO users (username, email, password, is_admin)
VALUES ('admin', 'admin@shop.com', 'admin123', 1)
""")

categories = [
    ('Electronics',),
    ('Food',),
    ('Books',),
    ('Clothes',),
    ('Toys',)
]

c.executemany(
    "INSERT INTO categories (name) VALUES (?)",
    categories
)

products = [
    ('Laptop', 800, 'laptop.jpg', 1),
    ('Phone', 500, 'phone.jpg', 1),
    ('Headphones', 120, 'headphones.jpg', 1),
    ('TV', 900, 'tv.jpg', 1),
    ('Camera', 650, 'camera.jpg', 1),

    ('Pizza', 10, 'pizza.jpg', 2),
    ('Burger', 8, 'burger.jpg', 2),
    ('Apple', 1, 'apple.jpg', 2),
    ('Orange', 2, 'orange.jpg', 2),
    ('Pasta', 6, 'pasta.jpg', 2),

    ('Novel', 15, 'novel.jpg', 3),
    ('Comics', 12, 'comics.jpg', 3),
    ('Dictionary', 25, 'dictionary.jpg', 3),
    ('Textbook', 40, 'textbook.jpg', 3),

    ('T-shirt', 20, 'tshirt.jpg', 4),
    ('Jacket', 80, 'jacket.jpg', 4),
    ('Jeans', 50, 'jeans.jpg', 4),
    ('Shoes', 70, 'shoes.jpg', 4),

    ('Toy Car', 25, 'toycar.jpg', 5),
    ('Doll', 30, 'doll.jpg', 5),
    ('Puzzle', 18, 'puzzle.jpg', 5),
]

c.executemany(
    "INSERT INTO products (name, price, image, category_id) VALUES (?,?,?,?)",
    products
)

db.commit()
db.close()

print("SHOP DATA READY")
