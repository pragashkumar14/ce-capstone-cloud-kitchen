from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from db import get_connection

app = Flask(__name__)
app.secret_key = "dev-secret-change-me"  # fine for now, not security-sensitive (no auth, no PII beyond a name)

COURSES = ["starters", "main", "desserts", "drinks"]


@app.route("/")
def menu():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM menu_items WHERE available = TRUE ORDER BY course, name"
    )
    items = cur.fetchall()
    conn.close()

    menu_by_course = {c: [] for c in COURSES}
    for item in items:
        menu_by_course[item["course"]].append(item)

    return render_template("menu.html", menu_by_course=menu_by_course, courses=COURSES)


@app.route("/cart/add", methods=["POST"])
def add_to_cart():
    item_id = request.form["item_id"]
    quantity = int(request.form.get("quantity", 1))

    cart = session.get("cart", {})
    cart[item_id] = cart.get(item_id, 0) + quantity
    session["cart"] = cart

    return redirect(url_for("menu"))


@app.route("/cart")
def view_cart():
    cart = session.get("cart", {})
    if not cart:
        return render_template("cart.html", items=[], total_cents=0)

    conn = get_connection()
    cur = conn.cursor()
    ids = tuple(int(i) for i in cart.keys())
    cur.execute("SELECT * FROM menu_items WHERE id = ANY(%s)", (list(ids),))
    rows = {str(row["id"]): row for row in cur.fetchall()}
    conn.close()

    items = []
    total_cents = 0
    for item_id, qty in cart.items():
        row = rows.get(item_id)
        if not row:
            continue
        subtotal = row["price_cents"] * qty
        total_cents += subtotal
        items.append({**row, "quantity": qty, "subtotal_cents": subtotal})

    return render_template("cart.html", items=items, total_cents=total_cents)


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    cart = session.get("cart", {})
    if not cart:
        return redirect(url_for("menu"))

    if request.method == "GET":
        return render_template("checkout.html")

    customer_name = request.form["customer_name"]
    pickup_time = request.form["pickup_time"]

    conn = get_connection()
    cur = conn.cursor()
    ids = tuple(int(i) for i in cart.keys())
    cur.execute("SELECT * FROM menu_items WHERE id = ANY(%s)", (list(ids),))
    rows = {str(row["id"]): row for row in cur.fetchall()}

    total_cents = sum(rows[i]["price_cents"] * qty for i, qty in cart.items() if i in rows)

    cur.execute(
        "INSERT INTO orders (customer_name, pickup_time, total_cents) VALUES (%s, %s, %s) RETURNING id",
        (customer_name, pickup_time, total_cents),
    )
    order_id = cur.fetchone()["id"]

    for item_id, qty in cart.items():
        if item_id not in rows:
            continue
        cur.execute(
            "INSERT INTO order_items (order_id, menu_item_id, quantity, price_cents_at_order) VALUES (%s, %s, %s, %s)",
            (order_id, int(item_id), qty, rows[item_id]["price_cents"]),
        )

    conn.commit()
    conn.close()
    session.pop("cart", None)

    return render_template("confirmation.html", order_id=order_id, pickup_time=pickup_time)


@app.route("/health")
def health():
    try:
        conn = get_connection()
        conn.close()
        return jsonify(status="healthy"), 200
    except Exception as e:
        return jsonify(status="unhealthy", error=str(e)), 503


@app.route("/kitchen")
def kitchen():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT o.id, o.customer_name, o.pickup_time, o.status, o.total_cents, "
        "array_agg(mi.name || ' x' || oi.quantity) AS item_summary "
        "FROM orders o "
        "JOIN order_items oi ON oi.order_id = o.id "
        "JOIN menu_items mi ON mi.id = oi.menu_item_id "
        "WHERE o.status != 'completed' "
        "GROUP BY o.id "
        "ORDER BY o.created_at DESC"
    )
    orders = cur.fetchall()
    conn.close()
    return render_template("kitchen.html", orders=orders)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
