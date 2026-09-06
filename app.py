from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)

# Secret key for login sessions
app.secret_key = "CHANGE_THIS_TO_A_LONG_RANDOM_SECRET"

DB_NAME = "velloria.db"


# =========================
# DATABASE CONNECTION
# =========================

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


# =========================
# CREATE DATABASE TABLES
# =========================

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


# =========================
# LOGIN CHECK
# =========================

def logged_in():
    return "customer_id" in session


# =========================
# HOME PAGE
# =========================

@app.route("/")
def home():
    return render_template("index.html")


# =========================
# CART PAGE
# =========================

@app.route("/cart")
def cart():
    return render_template("cart.html")


# =========================
# LOGIN PAGE
# =========================

@app.route("/login")
def login():

    if logged_in():
        return redirect(url_for("checkout"))

    return render_template("login.html")


# =========================
# CHECKOUT PAGE
# =========================

@app.route("/checkout")
def checkout():

    if not logged_in():
        return redirect(url_for("login", next="checkout"))

    return render_template("checkout.html")


# =========================
# MY ORDERS
# =========================

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

    return render_template("orders.html", orders=rows)


# =========================
# ORDER TRACKING
# =========================

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
            (order_id, session["customer_id"])
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


# =========================
# PROFILE
# =========================

@app.route("/profile")
def profile():

    if not logged_in():
        return redirect(url_for("login"))

    conn = get_db()

    customer = conn.execute(
        """
        SELECT id,
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


# =========================
# CHECK LOGIN SESSION
# =========================

@app.route("/api/session")
def api_session():

    return jsonify({
        "logged_in": logged_in()
    })


# =========================
# SIGN UP
# =========================

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

    # Check required fields
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

    # Password validation
    if len(password) < 6:
        return jsonify({
            "ok": False,
            "message": "Password must contain at least 6 characters."
        }), 400

    conn = get_db()

    try:

        # Create customer
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

        # Save address
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

        # Login automatically after signup
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


# =========================
# LOGIN API
# =========================

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

    # Check login details
    if not customer or not check_password_hash(
        customer["password_hash"],
        password
    ):
        return jsonify({
            "ok": False,
            "message": "Invalid mobile number or password."
        }), 401

    # Clear old session
    session.clear()

    # Create new session
    session["customer_id"] = customer["id"]
    session["customer_name"] = customer["first_name"]

    return jsonify({
        "ok": True,
        "message": "Login successful."
    })


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))


# =========================
# CREATE ORDER
# =========================

@app.route("/api/create-order", methods=["POST"])
def create_order():

    # User must be logged in
    if not logged_in():

        return jsonify({
            "ok": False,
            "login_required": True
        }), 401

    data = request.get_json(silent=True) or {}

    items = data.get("items", [])

    # Check cart
    if not items:

        return jsonify({
            "ok": False,
            "message": "Cart is empty."
        }), 400

    total = 0
    clean_items = []

    # Validate cart items
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

        # Create order
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

        # Add order items
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

    except Exception as e:

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


# =========================
# START APPLICATION
# =========================

if __name__ == "__main__":

    init_db()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )