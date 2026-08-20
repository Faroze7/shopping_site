import os
import json
import sqlite3

import stripe

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify
)

from config import Config


app = Flask(__name__)
app.config.from_object(Config)

stripe.api_key = app.config["STRIPE_SECRET_KEY"]


# =========================================================
# PRODUCTS
# =========================================================

products = [
    {
        "id": 1,
        "name": "Premium Headphones",
        "description": "Wireless noise-cancelling headphones",
        "price": 4999,
        "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e"
    },
    {
        "id": 2,
        "name": "Smart Watch",
        "description": "Modern smartwatch with fitness tracking",
        "price": 7999,
        "image": "https://images.unsplash.com/photo-1523275335684-37898b6baf30"
    },
    {
        "id": 3,
        "name": "Premium Sneakers",
        "description": "Comfortable everyday sneakers",
        "price": 3499,
        "image": "https://images.unsplash.com/photo-1542291026-7eec264c27ff"
    },
    {
        "id": 4,
        "name": "Minimal Backpack",
        "description": "Stylish backpack for everyday use",
        "price": 2999,
        "image": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62"
    }
]


# =========================================================
# DATABASE
# =========================================================

DATABASE = os.path.join(
    os.path.dirname(__file__),
    "database",
    "shop.db"
)


def get_db():

    os.makedirs(
        os.path.dirname(DATABASE),
        exist_ok=True
    )

    connection = sqlite3.connect(DATABASE)

    connection.row_factory = sqlite3.Row

    return connection


def init_db():

    connection = get_db()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stripe_session_id TEXT UNIQUE,
            amount INTEGER NOT NULL,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    connection.commit()

    connection.close()


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def find_product(product_id):

    return next(
        (
            product
            for product in products
            if product["id"] == product_id
        ),
        None
    )


def get_cart_products():

    cart = session.get("cart", [])

    cart_products = []

    for product_id in cart:

        product = find_product(product_id)

        if product:
            cart_products.append(product)

    return cart_products


# =========================================================
# CART COUNT AVAILABLE TO ALL TEMPLATES
# =========================================================

@app.context_processor
def inject_cart_count():

    cart = session.get("cart", [])

    return {
        "cart_count": len(cart)
    }


# =========================================================
# HOME
# =========================================================

@app.route("/")
def index():

    return render_template(
        "index.html",
        products=products
    )


# =========================================================
# PRODUCT REST API
# =========================================================

@app.route("/api/products", methods=["GET"])
def get_products():

    return jsonify({
        "products": products
    })


@app.route(
    "/api/products/<int:product_id>",
    methods=["GET"]
)
def get_product(product_id):

    product = find_product(product_id)

    if not product:

        return jsonify({
            "error": "Product not found"
        }), 404

    return jsonify(product)


# =========================================================
# CART PAGE
# =========================================================

@app.route("/cart")
def cart():

    cart_products = get_cart_products()

    total = sum(
        product["price"]
        for product in cart_products
    )

    return render_template(
        "cart.html",
        cart=cart_products,
        total=total
    )


# =========================================================
# ADD TO CART REST API
# =========================================================

@app.route(
    "/api/cart/add",
    methods=["POST"]
)
def add_to_cart():

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify({
            "error": "Request body must contain JSON"
        }), 400

    product_id = data.get("product_id")

    if product_id is None:

        return jsonify({
            "error": "product_id is required"
        }), 400

    try:

        product_id = int(product_id)

    except (ValueError, TypeError):

        return jsonify({
            "error": "Invalid product_id"
        }), 400

    product = find_product(product_id)

    if not product:

        return jsonify({
            "error": "Product not found"
        }), 404

    cart = session.get(
        "cart",
        []
    )

    cart.append(product_id)

    session["cart"] = cart

    return jsonify({
        "message": "Product added to cart",
        "cart_count": len(cart)
    })


# =========================================================
# REMOVE FROM CART REST API
# =========================================================

@app.route(
    "/api/cart/remove/<int:product_id>",
    methods=["DELETE"]
)
def remove_from_cart(product_id):

    cart = session.get(
        "cart",
        []
    )

    if product_id not in cart:

        return jsonify({
            "error": "Product is not in cart"
        }), 404

    cart.remove(product_id)

    session["cart"] = cart

    return jsonify({
        "message": "Product removed from cart",
        "cart_count": len(cart)
    })


# =========================================================
# CLEAR CART
# =========================================================

@app.route(
    "/api/cart/clear",
    methods=["DELETE"]
)
def clear_cart():

    session.pop(
        "cart",
        None
    )

    return jsonify({
        "message": "Cart cleared",
        "cart_count": 0
    })


# =========================================================
# STRIPE CHECKOUT
# =========================================================

@app.route(
    "/checkout",
    methods=["POST"]
)
def checkout():

    cart_products = get_cart_products()

    if not cart_products:

        return redirect(
            url_for("cart")
        )

    line_items = []

    total = 0

    for product in cart_products:

        total += product["price"]

        line_items.append({

            "price_data": {

                "currency": "inr",

                "product_data": {
                    "name": product["name"]
                },

                # Stripe expects the smallest currency unit.
                # 4999 = ₹49.99
                "unit_amount": product["price"]
            },

            "quantity": 1
        })


    try:

        checkout_session = stripe.checkout.Session.create(

            payment_method_types=[
                "card"
            ],

            line_items=line_items,

            mode="payment",

            success_url=url_for(
                "payment_success",
                _external=True
            ) + "?session_id={CHECKOUT_SESSION_ID}",

            cancel_url=url_for(
                "payment_cancel",
                _external=True
            )
        )


        # Create pending order

        connection = get_db()

        connection.execute(
            """
            INSERT OR IGNORE INTO orders
            (
                stripe_session_id,
                amount,
                status
            )
            VALUES (?, ?, ?)
            """,
            (
                checkout_session.id,
                total,
                "pending"
            )
        )

        connection.commit()

        connection.close()


        return redirect(
            checkout_session.url,
            code=303
        )


    except stripe.error.StripeError as error:

        print(
            "Stripe error:",
            error
        )

        return redirect(
            url_for("cart")
        )


# =========================================================
# PAYMENT SUCCESS
# =========================================================

@app.route("/success")
def payment_success():

    session_id = request.args.get(
        "session_id"
    )

    if not session_id:

        return redirect(
            url_for("index")
        )


    try:

        checkout_session = stripe.checkout.Session.retrieve(
            session_id
        )


        if checkout_session.payment_status == "paid":

            # Clear this browser's cart only
            # after Stripe confirms payment.

            session.pop(
                "cart",
                None
            )

            return render_template(
                "success.html"
            )


        return render_template(
            "cancel.html"
        )


    except stripe.error.StripeError:

        return redirect(
            url_for("index")
        )


# =========================================================
# PAYMENT CANCEL
# =========================================================

@app.route("/cancel")
def payment_cancel():

    return render_template(
        "cancel.html"
    )


# =========================================================
# STRIPE WEBHOOK
# =========================================================

@app.route(
    "/webhook/stripe",
    methods=["POST"]
)
def stripe_webhook():

    payload = request.data

    signature = request.headers.get(
        "Stripe-Signature"
    )

    webhook_secret = app.config[
        "STRIPE_WEBHOOK_SECRET"
    ]

    try:

        event = stripe.Webhook.construct_event(

            payload,

            signature,

            webhook_secret
        )

    except ValueError:

        return "Invalid payload", 400

    except stripe.error.SignatureVerificationError:

        return "Invalid signature", 400


    # Payment completed

    if event["type"] == "checkout.session.completed":

        checkout_session = event[
            "data"
        ]["object"]

        session_id = checkout_session[
            "id"
        ]


        connection = get_db()

        connection.execute(
            """
            UPDATE orders
            SET status = ?
            WHERE stripe_session_id = ?
            """,
            (
                "paid",
                session_id
            )
        )

        connection.commit()

        connection.close()


    return "", 200


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    init_db()

    app.run(
        debug=True
    )