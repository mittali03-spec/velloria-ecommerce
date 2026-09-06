from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)

# ============================================================
# SECRET KEY
# ============================================================

app.secret_key = "velloria-project-secret-key-change-this-later"

DB_NAME = "velloria.db"


# ============================================================
# ADMIN LOGIN
# ============================================================

ADMIN_USERNAME = "Mittali03"
ADMIN_PASSWORD = "mittali@123"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================
# CREATE DATABASE TABLES
# ============================================================

def init_db():

    conn = get_db()

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            mobile TEXT NOT NULL UNIQUE,
            email TEXT UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS addresses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            address_line TEXT NOT NULL,
            city TEXT NOT NULL,
            state TEXT NOT NULL,
            pincode TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(customer_id) REFERENCES customers(id)
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            total_amount REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Placed',
            created_at TEXT NOT NULL,
            FOREIGN KEY(customer_id) REFERENCES customers(id)
        );

        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY(order_id) REFERENCES orders(id)
        );
    """)

    conn.commit()
    conn.close()


# ============================================================
# INITIALIZE DATABASE
# ============================================================

init_db()


# ============================================================
# CUSTOMER LOGIN CHECK
# ============================================================

def logged_in():
    return "customer_id" in session


# ============================================================
# ADMIN LOGIN CHECK
# ============================================================

def admin_logged_in():
    return session.get("admin_logged_in") is True


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def home():
    return render_template("index.html")


# ============================================================
# CART PAGE
# ============================================================

@app.route("/cart")
def cart():
    return render_template("cart.html")


# ============================================================
# CUSTOMER LOGIN PAGE
# ============================================================

@app.route("/login")
def login():

    if logged_in():
        return redirect(url_for("checkout"))

    return render_template("login.html")


# ============================================================
# CHECKOUT PAGE
# ============================================================

@app.route("/checkout")
def checkout():

    if not logged_in():
        return redirect(url_for("login", next="checkout"))

    return render_template("checkout.html")


# ============================================================
# MY ORDERS
# ============================================================

@app.route("/orders")
def orders():

    if not logged_in():
        return redirect(url_for("login"))

    conn = get_db()

    rows = conn.execute(
        """
        SELECT *
        FROM orders
        WHERE customer_id=?
        ORDER BY id DESC
        """,
        (session["customer_id"],)
    ).fetchall()

    conn.close()

    return render_template(
        "orders.html",
        orders=rows
    )


# ============================================================
# ORDER TRACKING
# ============================================================

@app.route("/order-tracking")
def order_tracking():

    if not logged_in():
        return redirect(url_for("login"))

    order_id = request.args.get("order_id", type=int)

    conn = get_db()

    order = None
    items = []

    if order_id:

        order = conn.execute(
            """
            SELECT *
            FROM orders
            WHERE id=? AND customer_id=?
            """,
            (
                order_id,
                session["customer_id"]
            )
        ).fetchone()

        if order:

            items = conn.execute(
                """
                SELECT *
                FROM order_items
                WHERE order_id=?
                """,
                (order_id,)
            ).fetchall()

    conn.close()

    return render_template(
        "order_tracking.html",
        order=order,
        items=items
    )


# ============================================================
# PROFILE
# ============================================================

@app.route("/profile")
def profile():

    if not logged_in():
        return redirect(url_for("login"))

    conn = get_db()

    customer = conn.execute(
        """
        SELECT
            id,
            first_name,
            last_name,
            mobile,
            email,
            created_at
        FROM customers
        WHERE id=?
        """,
        (session["customer_id"],)
    ).fetchone()

    address = conn.execute(
        """
        SELECT *
        FROM addresses
        WHERE customer_id=?
        ORDER BY id DESC
        LIMIT 1
        """,
        (session["customer_id"],)
    ).fetchone()

    conn.close()

    return render_template(
        "profile.html",
        customer=customer,
        address=address
    )


# ============================================================
# CUSTOMER SESSION API
# ============================================================

@app.route("/api/session")
def api_session():

    return jsonify({
        "logged_in": logged_in()
    })


# ============================================================
# CUSTOMER SIGN UP
# ============================================================

@app.route("/api/signup", methods=["POST"])
def api_signup():

    data = request.get_json(silent=True) or {}

    first = data.get("first_name", "").strip()
    last = data.get("last_name", "").strip()
    mobile = data.get("mobile", "").strip()
    email = data.get("email", "").strip() or None
    password = data.get("password", "")

    address = data.get("address", "").strip()
    city = data.get("city", "").strip()
    state = data.get("state", "").strip()
    pincode = data.get("pincode", "").strip()

    if not all([
        first,
        last,
        mobile,
        password,
        address,
        city,
        state,
        pincode
    ]):

        return jsonify({
            "ok": False,
            "message": "Please fill all required fields."
        }), 400

    if len(password) < 6:

        return jsonify({
            "ok": False,
            "message": "Password must contain at least 6 characters."
        }), 400

    conn = get_db()

    try:

        cur = conn.execute(
            """
            INSERT INTO customers
            (
                first_name,
                last_name,
                mobile,
                email,
                password_hash,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                first,
                last,
                mobile,
                email,
                generate_password_hash(password),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        )

        customer_id = cur.lastrowid

        conn.execute(
            """
            INSERT INTO addresses
            (
                customer_id,
                address_line,
                city,
                state,
                pincode,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                customer_id,
                address,
                city,
                state,
                pincode,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        )

        conn.commit()

        session.clear()

        session["customer_id"] = customer_id
        session["customer_name"] = first

        return jsonify({
            "ok": True,
            "message": "Account created successfully."
        })

    except sqlite3.IntegrityError:

        conn.rollback()

        return jsonify({
            "ok": False,
            "message": "Mobile or email is already registered."
        }), 409

    finally:

        conn.close()


# ============================================================
# CUSTOMER LOGIN API
# ============================================================

@app.route("/api/login", methods=["POST"])
def api_login():

    data = request.get_json(silent=True) or {}

    mobile = data.get("mobile", "").strip()
    password = data.get("password", "")

    conn = get_db()

    customer = conn.execute(
        """
        SELECT *
        FROM customers
        WHERE mobile=?
        """,
        (mobile,)
    ).fetchone()

    conn.close()

    if not customer or not check_password_hash(
        customer["password_hash"],
        password
    ):

        return jsonify({
            "ok": False,
            "message": "Invalid mobile number or password."
        }), 401

    session.clear()

    session["customer_id"] = customer["id"]
    session["customer_name"] = customer["first_name"]

    return jsonify({
        "ok": True,
        "message": "Login successful."
    })


# ============================================================
# CUSTOMER LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))


# ============================================================
# CREATE ORDER
# ============================================================

@app.route("/api/create-order", methods=["POST"])
def create_order():

    if not logged_in():

        return jsonify({
            "ok": False,
            "login_required": True
        }), 401

    data = request.get_json(silent=True) or {}

    items = data.get("items", [])

    if not items:

        return jsonify({
            "ok": False,
            "message": "Cart is empty."
        }), 400

    total = 0
    clean_items = []

    for item in items:

        name = str(
            item.get("name", "")
        ).strip()

        try:

            price = float(
                item.get("price", 0)
            )

            qty = int(
                item.get("quantity", 0)
            )

        except (ValueError, TypeError):

            return jsonify({
                "ok": False,
                "message": "Invalid cart item."
            }), 400

        if not name or price < 0 or qty <= 0:

            return jsonify({
                "ok": False,
                "message": "Invalid cart item."
            }), 400

        total += price * qty

        clean_items.append(
            (
                name,
                price,
                qty
            )
        )

    conn = get_db()

    try:

        cur = conn.execute(
            """
            INSERT INTO orders
            (
                customer_id,
                total_amount,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                session["customer_id"],
                total,
                "Placed",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        )

        order_id = cur.lastrowid

        conn.executemany(
            """
            INSERT INTO order_items
            (
                order_id,
                product_name,
                price,
                quantity
            )
            VALUES (?, ?, ?, ?)
            """,
            [
                (
                    name,
                    price,
                    qty
                )
                for name, price, qty in clean_items
            ]
        )

        # Fix order_id for each order item
        conn.execute(
            """
            DELETE FROM order_items
            WHERE order_id=?
            """,
            (order_id,)
        )

        conn.executemany(
            """
            INSERT INTO order_items
            (
                order_id,
                product_name,
                price,
                quantity
            )
            VALUES (?, ?, ?, ?)
            """,
            [
                (
                    order_id,
                    name,
                    price,
                    qty
                )
                for name, price, qty in clean_items
            ]
        )

        conn.commit()

    except Exception:

        conn.rollback()

        return jsonify({
            "ok": False,
            "message": "Could not create order."
        }), 500

    finally:

        conn.close()

    return jsonify({
        "ok": True,
        "order_id": order_id,
        "total": total
    })


# ============================================================
# ============================================================
# ADMIN SYSTEM
# ============================================================
# ============================================================


# ============================================================
# ADMIN LOGIN PAGE
# ============================================================

@app.route("/admin/login")
def admin_login():

    if admin_logged_in():
        return redirect(url_for("admin_dashboard"))

    return render_template("admin_login.html")


# ============================================================
# ADMIN LOGIN API
# ============================================================

@app.route("/admin/login", methods=["POST"])
def admin_login_submit():

    username = request.form.get(
        "username",
        ""
    ).strip()

    password = request.form.get(
        "password",
        ""
    )

    if (
        username == ADMIN_USERNAME
        and password == ADMIN_PASSWORD
    ):

        session.clear()

        session["admin_logged_in"] = True
        session["admin_username"] = ADMIN_USERNAME

        return redirect(
            url_for("admin_dashboard")
        )

    return render_template(
        "admin_login.html",
        error="Invalid admin username or password."
    )


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@app.route("/admin/dashboard")
def admin_dashboard():

    if not admin_logged_in():

        return redirect(
            url_for("admin_login")
        )

    conn = get_db()

    # Total customers
    total_customers = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM customers
        """
    ).fetchone()["count"]

    # Total orders
    total_orders = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM orders
        """
    ).fetchone()["count"]

    # Total sales
    total_sales = conn.execute(
        """
        SELECT COALESCE(SUM(total_amount), 0) AS total
        FROM orders
        """
    ).fetchone()["total"]

    # Pending orders
    pending_orders = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM orders
        WHERE status IN ('Placed', 'Processing', 'Shipped')
        """
    ).fetchone()["count"]

    # All customers
    customers = conn.execute(
        """
        SELECT
            c.id,
            c.first_name,
            c.last_name,
            c.mobile,
            c.email,
            c.created_at,
            a.address_line,
            a.city,
            a.state,
            a.pincode
        FROM customers c
        LEFT JOIN addresses a
            ON a.id = (
                SELECT MAX(a2.id)
                FROM addresses a2
                WHERE a2.customer_id = c.id
            )
        ORDER BY c.id DESC
        """
    ).fetchall()

    # All orders
    orders = conn.execute(
        """
        SELECT
            o.id,
            o.customer_id,
            o.total_amount,
            o.status,
            o.created_at,
            c.first_name,
            c.last_name,
            c.mobile
        FROM orders o
        JOIN customers c
            ON o.customer_id = c.id
        ORDER BY o.id DESC
        """
    ).fetchall()

    conn.close()

    return render_template(
        "admin_dashboard.html",
        total_customers=total_customers,
        total_orders=total_orders,
        total_sales=total_sales,
        pending_orders=pending_orders,
        customers=customers,
        orders=orders
    )


# ============================================================
# ADMIN ORDER DETAILS
# ============================================================

@app.route("/admin/order/<int:order_id>")
def admin_order_details(order_id):

    if not admin_logged_in():

        return redirect(
            url_for("admin_login")
        )

    conn = get_db()

    order = conn.execute(
        """
        SELECT
            o.*,
            c.first_name,
            c.last_name,
            c.mobile,
            c.email
        FROM orders o
        JOIN customers c
            ON o.customer_id = c.id
        WHERE o.id=?
        """,
        (order_id,)
    ).fetchone()

    items = conn.execute(
        """
        SELECT *
        FROM order_items
        WHERE order_id=?
        """,
        (order_id,)
    ).fetchall()

    address = None

    if order:

        address = conn.execute(
            """
            SELECT *
            FROM addresses
            WHERE customer_id=?
            ORDER BY id DESC
            LIMIT 1
            """,
            (order["customer_id"],)
        ).fetchone()

    conn.close()

    if not order:

        return "Order not found", 404

    return render_template(
        "admin_order_details.html",
        order=order,
        items=items,
        address=address
    )


# ============================================================
# UPDATE ORDER STATUS
# ============================================================

@app.route(
    "/admin/order/<int:order_id>/status",
    methods=["POST"]
)
def update_order_status(order_id):

    if not admin_logged_in():

        return redirect(
            url_for("admin_login")
        )

    status = request.form.get(
        "status",
        ""
    ).strip()

    allowed_statuses = [
        "Placed",
        "Processing",
        "Shipped",
        "Out for Delivery",
        "Delivered",
        "Cancelled"
    ]

    if status not in allowed_statuses:

        return redirect(
            url_for(
                "admin_order_details",
                order_id=order_id
            )
        )

    conn = get_db()

    conn.execute(
        """
        UPDATE orders
        SET status=?
        WHERE id=?
        """,
        (
            status,
            order_id
        )
    )

    conn.commit()
    conn.close()

    return redirect(
        url_for(
            "admin_order_details",
            order_id=order_id
        )
    )


# ============================================================
# ADMIN LOGOUT
# ============================================================

@app.route("/admin/logout")
def admin_logout():

    session.clear()

    return redirect(
        url_for("admin_login")
    )


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )