from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)

app.secret_key = "velloria-project-secret-key-change-this-later"

DB_NAME = "velloria.db"

ADMIN_USERNAME = "Mittali03"
ADMIN_PASSWORD = "mittali@123"


# =========================================================
# DATABASE
# =========================================================

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


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
            customer_order_no INTEGER,
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

    # =====================================================
    # DATABASE MIGRATION
    # =====================================================

    columns = conn.execute(
        "PRAGMA table_info(orders)"
    ).fetchall()

    column_names = [column["name"] for column in columns]

    if "customer_order_no" not in column_names:

        conn.execute("""
            ALTER TABLE orders
            ADD COLUMN customer_order_no INTEGER
        """)

        # Give existing orders customer-wise order numbers
        customers = conn.execute("""
            SELECT DISTINCT customer_id
            FROM orders
            ORDER BY customer_id
        """).fetchall()

        for customer in customers:

            customer_id = customer["customer_id"]

            old_orders = conn.execute("""
                SELECT id
                FROM orders
                WHERE customer_id = ?
                ORDER BY id ASC
            """, (customer_id,)).fetchall()

            order_number = 1

            for order in old_orders:

                conn.execute("""
                    UPDATE orders
                    SET customer_order_no = ?
                    WHERE id = ?
                """, (
                    order_number,
                    order["id"]
                ))

                order_number += 1

    conn.commit()
    conn.close()


init_db()


# =========================================================
# LOGIN HELPERS
# =========================================================

def logged_in():
    return "customer_id" in session


def admin_logged_in():
    return session.get("admin_logged_in") is True


# =========================================================
# CUSTOMER PAGES
# =========================================================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/cart")
def cart():
    return render_template("cart.html")


@app.route("/login")
def login():

    if logged_in():

        next_page = request.args.get("next")

        if next_page == "checkout":
            return redirect(url_for("checkout"))

        return redirect(url_for("home"))

    return render_template("login.html")


@app.route("/checkout")
def checkout():

    if not logged_in():
        return redirect(
            url_for("login", next="checkout")
        )

    return render_template("checkout.html")


# =========================================================
# MY ORDERS
# =========================================================

@app.route("/orders")
def orders():

    if not logged_in():
        return redirect(url_for("login"))

    customer_id = session.get("customer_id")

    conn = get_db()

    try:

        customer = conn.execute("""
            SELECT *
            FROM customers
            WHERE id = ?
        """, (customer_id,)).fetchone()

        if not customer:

            session.clear()

            return redirect(url_for("login"))

        order_rows = conn.execute("""
            SELECT
                id,
                customer_id,
                customer_order_no,
                total_amount,
                status,
                created_at
            FROM orders
            WHERE customer_id = ?
            ORDER BY id DESC
        """, (customer_id,)).fetchall()

        customer_orders = list(order_rows)

        print("----------------------------------------")
        print("MY ORDERS")
        print("Customer ID:", customer_id)
        print(
            "Customer:",
            customer["first_name"],
            customer["last_name"]
        )
        print(
            "Number of Orders:",
            len(customer_orders)
        )

        for order in customer_orders:

            print(
                "Order #",
                order["customer_order_no"],
                "| Database ID:",
                order["id"],
                "| Customer ID:",
                order["customer_id"],
                "| Total:",
                order["total_amount"],
                "| Status:",
                order["status"]
            )

        print("----------------------------------------")

    finally:
        conn.close()

    return render_template(
        "orders.html",
        orders=customer_orders,
        customer=customer
    )


# =========================================================
# ORDER TRACKING
# =========================================================

@app.route("/order-tracking")
def order_tracking():

    if not logged_in():
        return redirect(url_for("login"))

    order_id = request.args.get(
        "order_id",
        type=int
    )

    customer_id = session.get("customer_id")

    conn = get_db()

    order = None
    items = []

    if order_id:

        order = conn.execute("""
            SELECT
                o.*,
                c.first_name,
                c.last_name,
                c.mobile
            FROM orders o
            JOIN customers c
                ON o.customer_id = c.id
            WHERE o.id = ?
            AND o.customer_id = ?
        """, (
            order_id,
            customer_id
        )).fetchone()

        if order:

            items = conn.execute("""
                SELECT *
                FROM order_items
                WHERE order_id = ?
                ORDER BY id
            """, (order_id,)).fetchall()

    conn.close()

    return render_template(
        "order_tracking.html",
        order=order,
        items=items
    )


# =========================================================
# PROFILE
# =========================================================

@app.route("/profile")
def profile():

    if not logged_in():
        return redirect(url_for("login"))

    customer_id = session.get("customer_id")

    conn = get_db()

    customer = conn.execute("""
        SELECT
            id,
            first_name,
            last_name,
            mobile,
            email,
            created_at
        FROM customers
        WHERE id = ?
    """, (customer_id,)).fetchone()

    address = conn.execute("""
        SELECT *
        FROM addresses
        WHERE customer_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, (customer_id,)).fetchone()

    conn.close()

    if not customer:

        session.clear()

        return redirect(url_for("login"))

    return render_template(
        "profile.html",
        customer=customer,
        address=address
    )


# =========================================================
# SESSION API
# =========================================================

@app.route("/api/session")
def api_session():

    return jsonify({
        "logged_in": logged_in(),
        "customer_name": session.get(
            "customer_name",
            ""
        ),
        "customer_id": session.get(
            "customer_id"
        )
    })


# =========================================================
# CUSTOMER SIGNUP
# =========================================================

@app.route("/api/signup", methods=["POST"])
def api_signup():

    data = request.get_json(silent=True) or {}

    first = str(
        data.get("first_name", "")
    ).strip()

    last = str(
        data.get("last_name", "")
    ).strip()

    mobile = str(
        data.get("mobile", "")
    ).strip()

    email = str(
        data.get("email", "")
    ).strip() or None

    password = str(
        data.get("password", "")
    )

    address = str(
        data.get("address", "")
    ).strip()

    city = str(
        data.get("city", "")
    ).strip()

    state = str(
        data.get("state", "")
    ).strip()

    pincode = str(
        data.get("pincode", "")
    ).strip()

    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

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

    if not mobile.isdigit():

        return jsonify({
            "ok": False,
            "message": "Please enter a valid mobile number."
        }), 400

    if len(mobile) != 10:

        return jsonify({
            "ok": False,
            "message": "Mobile number must contain 10 digits."
        }), 400

    if not pincode.isdigit() or len(pincode) != 6:

        return jsonify({
            "ok": False,
            "message": "Pincode must contain 6 digits."
        }), 400

    conn = get_db()

    try:

        existing_mobile = conn.execute("""
            SELECT id
            FROM customers
            WHERE mobile = ?
        """, (mobile,)).fetchone()

        if existing_mobile:

            return jsonify({
                "ok": False,
                "message":
                    "This mobile number is already registered. Please login."
            }), 409

        if email:

            existing_email = conn.execute("""
                SELECT id
                FROM customers
                WHERE email = ?
            """, (email,)).fetchone()

            if existing_email:

                return jsonify({
                    "ok": False,
                    "message":
                        "This email is already registered. Please use another email."
                }), 409

        current_time = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        password_hash = generate_password_hash(
            password
        )

        cursor = conn.execute("""
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
        """, (
            first,
            last,
            mobile,
            email,
            password_hash,
            current_time
        ))

        customer_id = cursor.lastrowid

        conn.execute("""
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
        """, (
            customer_id,
            address,
            city,
            state,
            pincode,
            current_time
        ))

        conn.commit()

        session.clear()

        session["customer_id"] = customer_id
        session["customer_name"] = first

        return jsonify({
            "ok": True,
            "message": "Account created successfully.",
            "customer_id": customer_id
        })

    except sqlite3.IntegrityError as e:

        conn.rollback()

        print(
            "SIGNUP DATABASE ERROR:",
            e
        )

        return jsonify({
            "ok": False,
            "message":
                "This mobile number or email is already registered."
        }), 409

    except Exception as e:

        conn.rollback()

        print(
            "SIGNUP ERROR:",
            e
        )

        return jsonify({
            "ok": False,
            "message":
                "Unable to create account. Please try again."
        }), 500

    finally:
        conn.close()


# =========================================================
# CUSTOMER LOGIN
# =========================================================

@app.route("/api/login", methods=["POST"])
def api_login():

    data = request.get_json(silent=True) or {}

    mobile = str(
        data.get("mobile", "")
    ).strip()

    password = str(
        data.get("password", "")
    )

    if not mobile or not password:

        return jsonify({
            "ok": False,
            "message":
                "Please enter mobile number and password."
        }), 400

    conn = get_db()

    customer = conn.execute("""
        SELECT *
        FROM customers
        WHERE mobile = ?
    """, (mobile,)).fetchone()

    conn.close()

    if not customer:

        return jsonify({
            "ok": False,
            "message":
                "No account found with this mobile number."
        }), 401

    if not check_password_hash(
        customer["password_hash"],
        password
    ):

        return jsonify({
            "ok": False,
            "message":
                "Incorrect password."
        }), 401

    session.clear()

    session["customer_id"] = customer["id"]
    session["customer_name"] = customer["first_name"]

    return jsonify({
        "ok": True,
        "message": "Login successful.",
        "customer_id": customer["id"]
    })


# =========================================================
# CUSTOMER LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))


# =========================================================
# CREATE ORDER
# =========================================================

@app.route("/api/create-order", methods=["POST"])
def create_order():

    if not logged_in():

        return jsonify({
            "ok": False,
            "login_required": True,
            "message":
                "Please login before placing your order."
        }), 401

    customer_id = session.get("customer_id")

    data = request.get_json(silent=True) or {}

    items = data.get("items", [])

    if not isinstance(items, list) or not items:

        return jsonify({
            "ok": False,
            "message": "Cart is empty."
        }), 400

    total = 0
    clean_items = []

    for item in items:

        if not isinstance(item, dict):

            return jsonify({
                "ok": False,
                "message": "Invalid cart item."
            }), 400

        name = str(
            item.get("name", "")
        ).strip()

        try:

            price = float(
                item.get("price", 0)
            )

            quantity = int(
                item.get("quantity", 0)
            )

        except (ValueError, TypeError):

            return jsonify({
                "ok": False,
                "message": "Invalid cart item."
            }), 400

        if not name:

            return jsonify({
                "ok": False,
                "message": "Product name is missing."
            }), 400

        if price < 0:

            return jsonify({
                "ok": False,
                "message": "Invalid product price."
            }), 400

        if quantity <= 0:

            return jsonify({
                "ok": False,
                "message": "Invalid product quantity."
            }), 400

        total += price * quantity

        clean_items.append(
            (
                name,
                price,
                quantity
            )
        )

    conn = get_db()

    try:

        current_time = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        # -------------------------------------------------
        # GET NEXT ORDER NUMBER FOR THIS CUSTOMER
        # -------------------------------------------------
        # Every customer starts from Order #1.
        # Example:
        # Customer 1 -> #1, #2, #3
        # Customer 2 -> #1, #2
        # Customer 3 -> #1
        # -------------------------------------------------

        order_count = conn.execute("""
            SELECT COUNT(*) AS count
            FROM orders
            WHERE customer_id = ?
        """, (customer_id,)).fetchone()["count"]

        customer_order_no = order_count + 1
        # -------------------------------------------------
        # CREATE ORDER
        # -------------------------------------------------

        cursor = conn.execute("""
            INSERT INTO orders
            (
                customer_id,
                customer_order_no,
                total_amount,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            customer_id,
            customer_order_no,
            total,
            "Placed",
            current_time
        ))

        order_id = cursor.lastrowid

        # -------------------------------------------------
        # CREATE ORDER ITEMS
        # -------------------------------------------------

        for name, price, quantity in clean_items:

            conn.execute("""
                INSERT INTO order_items
                (
                    order_id,
                    product_name,
                    price,
                    quantity
                )
                VALUES (?, ?, ?, ?)
            """, (
                order_id,
                name,
                price,
                quantity
            ))

        conn.commit()

        print("----------------------------------------")
        print("NEW ORDER CREATED")
        print(
            "Customer Order Number:",
            customer_order_no
        )
        print(
            "Database Order ID:",
            order_id
        )
        print(
            "Customer ID:",
            customer_id
        )
        print(
            "Total:",
            total
        )
        print("----------------------------------------")

    except Exception as e:

        print(
            "ORDER ERROR:",
            e
        )

        conn.rollback()

        return jsonify({
            "ok": False,
            "message":
                "Could not create order."
        }), 500

    finally:
        conn.close()

    return jsonify({
        "ok": True,
        "message":
            "Order placed successfully.",
        "order_id":
            order_id,
        "customer_order_no":
            customer_order_no,
        "total":
            total
    })


# =========================================================
# ADMIN LOGIN PAGE
# =========================================================

@app.route("/admin/login")
def admin_login():

    if admin_logged_in():

        return redirect(
            url_for("admin_dashboard")
        )

    return render_template(
        "admin_login.html"
    )


# =========================================================
# ADMIN LOGIN SUBMIT
# =========================================================

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


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin/dashboard")
def admin_dashboard():

    if not admin_logged_in():

        return redirect(
            url_for("admin_login")
        )

    conn = get_db()

    total_customers = conn.execute("""
        SELECT COUNT(*) AS count
        FROM customers
    """).fetchone()["count"]

    total_orders = conn.execute("""
        SELECT COUNT(*) AS count
        FROM orders
    """).fetchone()["count"]

    total_sales = conn.execute("""
        SELECT COALESCE(
            SUM(total_amount),
            0
        ) AS total
        FROM orders
    """).fetchone()["total"]

    pending_orders = conn.execute("""
        SELECT COUNT(*) AS count
        FROM orders
        WHERE status IN (
            'Placed',
            'Processing',
            'Shipped',
            'Out for Delivery'
        )
    """).fetchone()["count"]

    customers = conn.execute("""
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
    """).fetchall()

    admin_orders = conn.execute("""
        SELECT
            o.id,
            o.customer_id,
            o.customer_order_no,
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
    """).fetchall()

    conn.close()

    return render_template(
        "admin_dashboard.html",
        total_customers=total_customers,
        total_orders=total_orders,
        total_sales=total_sales,
        pending_orders=pending_orders,
        customers=customers,
        orders=admin_orders
    )


# =========================================================
# ADMIN ORDER DETAILS
# =========================================================

@app.route("/admin/order/<int:order_id>")
def admin_order_details(order_id):

    if not admin_logged_in():

        return redirect(
            url_for("admin_login")
        )

    conn = get_db()

    order = conn.execute("""
        SELECT
            o.*,
            c.first_name,
            c.last_name,
            c.mobile,
            c.email
        FROM orders o
        JOIN customers c
            ON o.customer_id = c.id
        WHERE o.id = ?
    """, (order_id,)).fetchone()

    if not order:

        conn.close()

        return "Order not found", 404

    items = conn.execute("""
        SELECT *
        FROM order_items
        WHERE order_id = ?
        ORDER BY id
    """, (order_id,)).fetchall()

    address = conn.execute("""
        SELECT *
        FROM addresses
        WHERE customer_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, (order["customer_id"],)).fetchone()

    conn.close()

    return render_template(
        "admin_order_details.html",
        order=order,
        items=items,
        address=address
    )


# =========================================================
# UPDATE ORDER STATUS
# =========================================================

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

    conn.execute("""
        UPDATE orders
        SET status = ?
        WHERE id = ?
    """, (
        status,
        order_id
    ))

    conn.commit()
    conn.close()

    return redirect(
        url_for(
            "admin_order_details",
            order_id=order_id
        )
    )


# =========================================================
# ADMIN LOGOUT
# =========================================================

@app.route("/admin/logout")
def admin_logout():

    session.clear()

    return redirect(
        url_for("admin_login")
    )


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )