from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from db import get_connection

app = Flask(__name__)
app.secret_key = "dev-secret-change-me"  # fine for now, not security-sensitive (no auth, no PII beyond a name)

RESTAURANT_ADDRESS = "9 avenue Buffon, 77290 Mitry-Mory"
MIN_PICKUP_LEAD_MINUTES = 30

COURSES = ["starters", "main", "desserts", "drinks"]

ITEM_ICONS = {
    "Vegetable Samosa": "🥟",
    "Chicken Rolls": "🌯",
    "Plain Naan": "🫓",
    "Cheese Naan": "🫓",
    "Caesar Salad": "🥗",
    "Greek Salad": "🥗",
    "Chicken Biryani": "🍛",
    "Veg Biryani": "🍛",
    "Margherita Pizza (Small)": "🍕",
    "Margherita Pizza (Medium)": "🍕",
    "Margherita Pizza (Large)": "🍕",
    "Pepperoni Pizza (Small)": "🍕",
    "Pepperoni Pizza (Medium)": "🍕",
    "Pepperoni Pizza (Large)": "🍕",
    "Classic Cheeseburger": "🍔",
    "Veggie Burger": "🍔",
    "Sri Lankan Chicken Fried Rice": "🍚",
    "Chicken Kottu Rotti": "🍲",
    "French Toast": "🍞",
    "Crepe": "🥞",
    "Chocolate Brownie": "🍫",
    "Tiramisu": "🍰",
    "Coca-Cola": "🥤",
    "Mango Lassi": "🥭",
    "Chocolate Milkshake": "🥤",
    "Vanilla Milkshake": "🥤",
    "Strawberry Milkshake": "🥤",
    "Orange Juice": "🍊",
    "Mango Juice": "🥭",
    "Sri Lankan Tea": "🍵",
}

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
        item = dict(item)
        item["icon"] = ITEM_ICONS.get(item["name"], "🍽️")
        menu_by_course[item["course"]].append(item)

    active_tab = request.args.get("tab", COURSES[0])
    return render_template("menu.html", menu_by_course=menu_by_course, courses=COURSES, active_tab=active_tab)




@app.route("/cart/add", methods=["POST"])
def add_to_cart():
    item_id = request.form["item_id"]
    quantity = int(request.form.get("quantity", 1))

    cart = session.get("cart", {})
    cart[item_id] = cart.get(item_id, 0) + quantity
    session["cart"] = cart

    course = request.form.get("course")
    return redirect(url_for("menu", tab=course) if course else url_for("menu"))

@app.route("/cart/update", methods=["POST"])
def update_cart():
    item_id = request.form["item_id"]
    quantity = int(request.form.get("quantity", 1))

    cart = session.get("cart", {})
    if quantity <= 0:
        cart.pop(item_id, None)
    else:
        cart[item_id] = quantity
    session["cart"] = cart

    return redirect(url_for("view_cart"))


@app.route("/cart/remove", methods=["POST"])
def remove_from_cart():
    item_id = request.form["item_id"]
    cart = session.get("cart", {})
    cart.pop(item_id, None)
    session["cart"] = cart

    return redirect(url_for("view_cart"))



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

    min_pickup = (datetime.now() + timedelta(minutes=MIN_PICKUP_LEAD_MINUTES)).strftime("%Y-%m-%dT%H:%M")

    if request.method == "GET":
        return render_template("checkout.html", min_pickup=min_pickup, restaurant_address=RESTAURANT_ADDRESS)

    customer_name = request.form["customer_name"]
    pickup_time_str = request.form["pickup_time"]
    customer_address = request.form.get("customer_address", "").strip()

    pickup_time = datetime.strptime(pickup_time_str, "%Y-%m-%dT%H:%M")
    earliest_allowed = datetime.now() + timedelta(minutes=MIN_PICKUP_LEAD_MINUTES)

    if pickup_time < earliest_allowed:
        return render_template(
            "checkout.html",
            min_pickup=min_pickup,
            restaurant_address=RESTAURANT_ADDRESS,
            error=f"Pickup time must be at least {MIN_PICKUP_LEAD_MINUTES} minutes from now.",
        )

    conn = get_connection()
    cur = conn.cursor()
    ids = tuple(int(i) for i in cart.keys())
    cur.execute("SELECT * FROM menu_items WHERE id = ANY(%s)", (list(ids),))
    rows = {str(row["id"]): row for row in cur.fetchall()}
    total_cents = sum(rows[i]["price_cents"] * qty for i, qty in cart.items() if i in rows)

    cur.execute(
        "INSERT INTO orders (customer_name, pickup_time, total_cents) VALUES (%s, %s, %s) RETURNING id",
        (customer_name, pickup_time_str, total_cents),
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

    try:
        import boto3
        cw = boto3.client("cloudwatch", region_name="eu-west-3")
        cw.put_metric_data(
            Namespace="PamKitchen/Sales",
            MetricData=[
                {"MetricName": "OrdersPlaced", "Value": 1, "Unit": "Count"},
                {"MetricName": "RevenueEUR", "Value": total_cents / 100, "Unit": "None"},
            ],
        )
    except Exception:
        pass  # never let a metrics failure break checkout


    directions_url = None
    if customer_address:
        from urllib.parse import quote
        directions_url = (
            "https://www.google.com/maps/dir/?api=1"
            f"&origin={quote(customer_address)}"
            f"&destination={quote(RESTAURANT_ADDRESS)}"
        )

    return render_template(
        "confirmation.html",
        order_id=order_id,
        pickup_time=pickup_time_str,
        restaurant_address=RESTAURANT_ADDRESS,
        directions_url=directions_url,
    )


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

@app.route("/kitchen/complete/<int:order_id>", methods=["POST"])
def complete_order(order_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE orders SET status = 'completed' WHERE id = %s",
        (order_id,),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("kitchen"))

@app.route("/kitchen/all")
def all_orders():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT o.id, o.customer_name, o.pickup_time, o.status, o.total_cents, "
        "array_agg(mi.name || ' x' || oi.quantity) AS item_summary "
        "FROM orders o "
        "JOIN order_items oi ON oi.order_id = o.id "
        "JOIN menu_items mi ON mi.id = oi.menu_item_id "
        "GROUP BY o.id "
        "ORDER BY o.created_at DESC"
    )
    orders = cur.fetchall()
    conn.close()
    return render_template("all_orders.html", orders=orders)



@app.route("/kitchen/api/orders")
def kitchen_orders_api():
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
    return jsonify([
        {
            "id": o["id"],
            "customer_name": o["customer_name"],
            "pickup_time": o["pickup_time"].isoformat() if o["pickup_time"] else None,
            "status": o["status"],
            "total_cents": o["total_cents"],
            "item_summary": o["item_summary"],
        }
        for o in orders
    ])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
