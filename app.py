from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "simple_shop_secret"


# =========================
# DATABASE CONNECTION
# =========================
def get_db():
    return sqlite3.connect(
        "database.db",
        timeout=10,
        check_same_thread=False
    )


# =========================
# CART COUNT (for header badge)
# =========================
def get_cart_count():
    if "user_id" not in session or session.get("is_admin"):
        return 0

    con = get_db()
    cur = con.cursor()

    count = cur.execute(
        "SELECT COALESCE(SUM(quantity), 0) FROM cart WHERE user_id=?",
        (session["user_id"],)
    ).fetchone()[0]

    con.close()
    return count


# =========================
# ROOT REDIRECT
# =========================
@app.route("/")
def index():
    if "user_id" in session:
        return redirect("/dashboard")
    return redirect("/login")


# =========================
# LOGIN PAGE
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        con = get_db()
        cur = con.cursor()

        user = cur.execute(
            "SELECT id, username, password, is_admin FROM users WHERE username=?",
            (username,)
        ).fetchone()

        con.close()

        if not user or user[2] != password:
            return render_template("auth/login.html", error="Invalid username or password")

        session.clear()
        session["user_id"] = user[0]
        session["username"] = user[1]
        session["is_admin"] = bool(user[3])

        return redirect("/admin" if session["is_admin"] else "/dashboard")

    return render_template("auth/login.html")


# =========================
# REGISTER PAGE
# =========================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        con = get_db()
        cur = con.cursor()

        exists = cur.execute(
            "SELECT id FROM users WHERE username=? OR email=?",
            (username, email)
        ).fetchone()

        if exists:
            con.close()
            return render_template("auth/register.html", error="Username or email already exists")

        cur.execute(
            "INSERT INTO users (username, email, password) VALUES (?,?,?)",
            (username, email, password)
        )

        con.commit()
        con.close()
        return redirect("/login")

    return render_template("auth/register.html")


# =========================
# RESET PASSWORD
# =========================
@app.route("/reset", methods=["GET", "POST"])
def reset():
    if request.method == "POST":
        con = get_db()
        cur = con.cursor()

        if "password" not in request.form:
            identifier = request.form.get("identifier")

            user = cur.execute(
                "SELECT id FROM users WHERE username=? OR email=?",
                (identifier, identifier)
            ).fetchone()

            con.close()

            if not user:
                return render_template("auth/reset.html", step="find", error="User not found")

            return render_template("auth/reset.html", step="new_password", identifier=identifier)

        identifier = request.form.get("identifier")
        password = request.form.get("password")
        password2 = request.form.get("password2")

        if password != password2:
            return render_template(
                "auth/reset.html",
                step="new_password",
                error="Passwords do not match",
                identifier=identifier
            )

        con = get_db()
        cur = con.cursor()

        cur.execute(
            "UPDATE users SET password=? WHERE username=? OR email=?",
            (password, identifier, identifier)
        )

        con.commit()
        con.close()
        return redirect("/login")

    return render_template("auth/reset.html", step="find")


# =========================
# DASHBOARD (HOME SHOP)
# =========================
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    con = get_db()
    cur = con.cursor()

    categories = cur.execute("SELECT id, name FROM categories").fetchall()
    products = cur.execute(
        "SELECT id, name, price, image FROM products ORDER BY RANDOM() LIMIT 8"
    ).fetchall()

    con.close()

    return render_template(
        "shop/home.html",
        categories=categories,
        products=products,
        is_admin=session.get("is_admin"),
        cart_count=get_cart_count()
    )


# =========================
# CART PAGE
# =========================
@app.route("/cart")
def cart():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    con = get_db()
    cur = con.cursor()

    items = cur.execute("""
        SELECT products.id, products.name, products.price, cart.quantity
        FROM cart
        JOIN products ON cart.product_id = products.id
        WHERE cart.user_id=?
    """, (user_id,)).fetchall()

    con.close()

    total = sum(i[2] * i[3] for i in items)

    return render_template(
        "shop/cart.html",
        items=items,
        total=total,
        cart_count=get_cart_count()
    )


# =========================
# ADD PRODUCT TO CART
# =========================
@app.route("/add_to_cart/<int:product_id>")
def add_to_cart(product_id):
    if "user_id" not in session:
        return redirect("/login")

    con = get_db()
    cur = con.cursor()

    item = cur.execute(
        "SELECT quantity FROM cart WHERE user_id=? AND product_id=?",
        (session["user_id"], product_id)
    ).fetchone()

    if item:
        cur.execute(
            "UPDATE cart SET quantity = quantity + 1 WHERE user_id=? AND product_id=?",
            (session["user_id"], product_id)
        )
    else:
        cur.execute(
            "INSERT INTO cart (user_id, product_id, quantity) VALUES (?,?,1)",
            (session["user_id"], product_id)
        )

    con.commit()
    con.close()
    return redirect(request.referrer or "/dashboard")


# =========================
# CART + / - / REMOVE
# =========================
@app.route("/cart/increase/<int:product_id>")
def cart_increase(product_id):
    con = get_db()
    cur = con.cursor()
    cur.execute(
        "UPDATE cart SET quantity = quantity + 1 WHERE user_id=? AND product_id=?",
        (session["user_id"], product_id)
    )
    con.commit()
    con.close()
    return redirect("/cart")


@app.route("/cart/decrease/<int:product_id>")
def cart_decrease(product_id):
    con = get_db()
    cur = con.cursor()

    item = cur.execute(
        "SELECT quantity FROM cart WHERE user_id=? AND product_id=?",
        (session["user_id"], product_id)
    ).fetchone()

    if item and item[0] > 1:
        cur.execute(
            "UPDATE cart SET quantity = quantity - 1 WHERE user_id=? AND product_id=?",
            (session["user_id"], product_id)
        )
    else:
        cur.execute(
            "DELETE FROM cart WHERE user_id=? AND product_id=?",
            (session["user_id"], product_id)
        )

    con.commit()
    con.close()
    return redirect("/cart")

@app.route("/cart/remove/<int:product_id>")
def cart_remove(product_id):
    if "user_id" not in session:
        return redirect("/login")

    con = get_db()
    cur = con.cursor()

    cur.execute(
        "DELETE FROM cart WHERE user_id=? AND product_id=?",
        (session["user_id"], product_id)
    )

    con.commit()
    con.close()

    return redirect("/cart")


# =========================
# CHECKOUT PAGE
# =========================
@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    con = get_db()
    cur = con.cursor()

    items = cur.execute("""
        SELECT products.name, products.price, cart.quantity
        FROM cart
        JOIN products ON cart.product_id = products.id
        WHERE cart.user_id=?
    """, (user_id,)).fetchall()

    if not items:
        con.close()
        return redirect("/cart")

    total = sum(i[1] * i[2] for i in items)

    if request.method == "POST":
        address = request.form["address"]
        card = request.form["card"]

        cur.execute(
            "INSERT INTO orders (user_id, address, card, total) VALUES (?,?,?,?)",
            (user_id, address, card, total)
        )

        order_id = cur.lastrowid

        for i in items:
            cur.execute(
                "INSERT INTO order_items (order_id, product_name, price, quantity) VALUES (?,?,?,?)",
                (order_id, i[0], i[1], i[2])
            )

        cur.execute("DELETE FROM cart WHERE user_id=?", (user_id,))
        con.commit()
        con.close()
        return redirect("/order-success")

    con.close()
    return render_template(
        "shop/checkout.html",
        items=items,
        total=total,
        cart_count=get_cart_count()
    )


# =========================
# ORDER SUCCESS PAGE
# =========================
@app.route("/order-success")
def order_success():
    return render_template(
        "shop/order_success.html",
        cart_count=get_cart_count()
    )


# =========================
# SEARCH PRODUCTS
# =========================
@app.route("/search")
def search():
    if "user_id" not in session:
        return redirect("/login")

    query = request.args.get("q", "").strip()

    con = get_db()
    cur = con.cursor()

    products = []
    if query:
        products = cur.execute("""
            SELECT id, name, price, image
            FROM products
            WHERE name LIKE ?
        """, (f"%{query}%",)).fetchall()

    con.close()

    return render_template(
        "shop/search.html",
        products=products,
        query=query,
        is_admin=session.get("is_admin"),
        cart_count=get_cart_count()
    )


# =========================
# CATEGORY PAGE
# =========================
@app.route("/category/<int:category_id>")
def category_page(category_id):
    con = get_db()
    cur = con.cursor()

    category = cur.execute(
        "SELECT id, name FROM categories WHERE id=?",
        (category_id,)
    ).fetchone()

    products = cur.execute(
        "SELECT id, name, price, image FROM products WHERE category_id=?",
        (category_id,)
    ).fetchall()

    con.close()

    return render_template(
        "shop/category.html",
        category=category,
        products=products,
        cart_count=get_cart_count()
    )

# =========================
# PROFILE (MY ACCOUNT)
# =========================
@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    con = get_db()
    cur = con.cursor()

    user = cur.execute(
        "SELECT username, email FROM users WHERE id=?",
        (user_id,)
    ).fetchone()

    orders = cur.execute(
        "SELECT id, total, address FROM orders WHERE user_id=?",
        (user_id,)
    ).fetchall()

    con.close()

    return render_template(
        "shop/profile.html",
        user=user,
        orders=orders,
        cart_count=get_cart_count()
    )

# =========================
# PROFILE EDIT
# =========================
@app.route("/profile/edit", methods=["GET", "POST"])
def profile_edit():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    con = get_db()
    cur = con.cursor()

    message = None

    if request.method == "POST":
        email = request.form.get("email")
        p1 = request.form.get("password1")
        p2 = request.form.get("password2")

        if email:
            cur.execute(
                "UPDATE users SET email=? WHERE id=?",
                (email, user_id)
            )
            message = "Email updated successfully"

        if p1 or p2:
            if p1 != p2:
                con.close()
                return render_template(
                    "shop/profile_edit.html",
                    error="Passwords do not match",
                    cart_count=get_cart_count()
                )

            cur.execute(
                "UPDATE users SET password=? WHERE id=?",
                (p1, user_id)
            )
            message = "Password updated successfully"

        con.commit()

    user = cur.execute(
        "SELECT username, email FROM users WHERE id=?",
        (user_id,)
    ).fetchone()

    con.close()

    return render_template(
        "shop/profile_edit.html",
        user=user,
        message=message,
        cart_count=get_cart_count()
    )

# =========================
# ADMIN: ORDERS LIST
# =========================
@app.route("/admin")
@app.route("/admin/orders")
def admin_orders():
    # Allow only logged-in admins
    if "user_id" not in session or not session.get("is_admin"):
        return redirect("/login")

    con = get_db()
    cur = con.cursor()

    # Get all orders with user info
    orders = cur.execute("""
        SELECT
            orders.id,
            users.username,
            orders.total,
            orders.address
        FROM orders
        JOIN users ON orders.user_id = users.id
        ORDER BY orders.id DESC
    """).fetchall()

    con.close()

    return render_template(
        "admin/orders.html",
        orders=orders,
        active_page="orders"
    )


# =========================
# ADMIN: USERS LIST
# =========================
@app.route("/admin/users")
def admin_users():
    # Allow only logged-in admins
    if "user_id" not in session or not session.get("is_admin"):
        return redirect("/login")

    con = get_db()
    cur = con.cursor()

    # Get all registered users
    users = cur.execute("""
        SELECT id, username, email, is_admin
        FROM users
        ORDER BY id
    """).fetchall()

    con.close()

    return render_template(
        "admin/users.html",
        users=users,
        active_page="users"
    )


# =========================
# ADMIN: ORDER DETAILS
# =========================
@app.route("/admin/order/<int:order_id>")
def admin_order_details(order_id):
    # Allow only logged-in admins
    if "user_id" not in session or not session.get("is_admin"):
        return redirect("/login")

    con = get_db()
    cur = con.cursor()

    # Get items for one order
    items = cur.execute("""
        SELECT product_name, price, quantity
        FROM order_items
        WHERE order_id=?
    """, (order_id,)).fetchall()

    con.close()

    return render_template(
        "admin/order_details.html",
        items=items,
        order_id=order_id,
        active_page="orders"
    )

# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run()
