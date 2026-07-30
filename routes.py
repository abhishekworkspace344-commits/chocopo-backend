from datetime import time, datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4
import hmac
import hashlib
import razorpay

RAZORPAY_KEY_ID     = "rzp_test_TG7ncmd38qYC6y"
RAZORPAY_KEY_SECRET = "DhWyE5EG1lTyWTR5EkyZTfJs"
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from extensions import db
from models import (
    Category,
    Product,
    TimeSlot,
    Order,
    OrderItem,
    Customer,
    Admin,
    FranchiseEnquiry,
    SupportMessage
)

api = Blueprint("api", __name__, url_prefix="/api")


def serialize_order(order):
    return {
        "id": order.id,
        "order_number": order.order_number,
        "status": order.order_status,
        "order_status": order.order_status,
        "customer": {
            "name": order.customer.full_name if order.customer else "Customer",
            "phone": order.customer.phone if order.customer else "",
            "email": order.customer.email if order.customer else None
        },
        "customer_name": order.customer.full_name if order.customer else "Customer",
        "customer_phone": order.customer.phone if order.customer else "",
        "customer_email": order.customer.email if order.customer else None,
        "order_type": order.order_type,
        "delivery_address": order.delivery_address,
        "scheduled_date": order.scheduled_date.isoformat(),
        "order_date": order.scheduled_date.isoformat(),
        "time_slot": order.time_slot.label if order.time_slot else None,
        "subtotal": float(order.subtotal),
        "delivery_fee": float(order.delivery_fee),
        "total_amount": float(order.total_amount),
        "payment_method": order.payment_method,
        "payment_status": order.payment_status,
        "notes": order.notes,
        "created_at": order.created_at.isoformat(),
        "items": [
            {
                "product_name": item.product_name,
                "quantity": item.quantity,
                "unit_price": float(item.unit_price),
                "total_price": float(item.total_price)
            }
            for item in order.items
        ]
    }


# ─────────────────────────────────────────────
# SEED
# ─────────────────────────────────────────────

@api.route("/seed", methods=["POST"])
def seed_database():
    if Category.query.first():
        return jsonify({"message": "Database already contains CHOCOPO menu data."}), 200

    beverages = Category(name="Beverages", image_url="https://images.unsplash.com/photo-1495474472287-4d71bcdd2085")
    desserts  = Category(name="Desserts",  image_url="https://images.unsplash.com/photo-1551024506-0bccd828d307")
    cakes     = Category(name="Cakes",     image_url="https://images.unsplash.com/photo-1578985545062-69928b1d9587")
    snacks    = Category(name="Snacks",    image_url="https://images.unsplash.com/photo-1621939514649-280e2aa8e570")

    db.session.add_all([beverages, desserts, cakes, snacks])
    db.session.commit()

    products = [
        Product(category_id=beverages.id, name="Classic Hot Chocolate",  description="Rich Belgian chocolate with steamed milk.",         price=Decimal("180.00"), image_url="https://images.unsplash.com/photo-1542990253-a781e04c0082", preparation_minutes=10, is_featured=True),
        Product(category_id=beverages.id, name="Cold Coffee",             description="Creamy cold coffee topped with chocolate drizzle.", price=Decimal("160.00"), image_url="https://images.unsplash.com/photo-1461023058943-07fcbe16d735", preparation_minutes=10, is_featured=True),
        Product(category_id=desserts.id,  name="Chocolate Brownie",       description="Warm fudgy brownie with dark chocolate chunks.",    price=Decimal("120.00"), image_url="https://images.unsplash.com/photo-1606313564200-e75d5e30476c", preparation_minutes=15, is_featured=True),
        Product(category_id=desserts.id,  name="Chocolate Cookie",        description="Soft baked cookie with chocolate chips.",           price=Decimal("80.00"),  image_url="https://images.unsplash.com/photo-1499636136210-6f4ee915583e", preparation_minutes=10),
        Product(category_id=cakes.id,     name="Choco Lava Cake",         description="Warm chocolate cake with a molten center.",         price=Decimal("220.00"), image_url="https://images.unsplash.com/photo-1578985545062-69928b1d9587", preparation_minutes=20, is_featured=True),
        Product(category_id=cakes.id,     name="Chocolate Truffle Slice", description="Premium chocolate truffle cake slice.",             price=Decimal("150.00"), image_url="https://images.unsplash.com/photo-1578985545062-69928b1d9587", preparation_minutes=15),
        Product(category_id=snacks.id,    name="Cheese Garlic Bread",     description="Toasted garlic bread with melted cheese.",          price=Decimal("140.00"), image_url="https://images.unsplash.com/photo-1621939514649-280e2aa8e570", preparation_minutes=15),
        Product(category_id=snacks.id,    name="Chocolate Waffle",        description="Fresh waffle topped with chocolate sauce.",         price=Decimal("200.00"), image_url="https://images.unsplash.com/photo-1562376552-0d160a2f238d", preparation_minutes=20),
    ]

    time_slots = [
        TimeSlot(label="6:00 AM - 6:30 AM",   start_time=time(6,  0),  end_time=time(6,  30), max_orders=10),
        TimeSlot(label="6:30 AM - 7:00 AM",   start_time=time(6,  30), end_time=time(7,  0),  max_orders=10),
        TimeSlot(label="7:00 AM - 7:30 AM",   start_time=time(7,  0),  end_time=time(7,  30), max_orders=12),
        TimeSlot(label="7:30 AM - 8:00 AM",   start_time=time(7,  30), end_time=time(8,  0),  max_orders=12),
        TimeSlot(label="8:00 AM - 8:30 AM",   start_time=time(8,  0),  end_time=time(8,  30), max_orders=12),
        TimeSlot(label="8:30 AM - 9:00 AM",   start_time=time(8,  30), end_time=time(9,  0),  max_orders=12),
        TimeSlot(label="9:00 AM - 9:30 AM",   start_time=time(9,  0),  end_time=time(9,  30), max_orders=15),
        TimeSlot(label="9:30 AM - 10:00 AM",  start_time=time(9,  30), end_time=time(10, 0),  max_orders=15),
        TimeSlot(label="10:00 AM - 10:30 AM", start_time=time(10, 0),  end_time=time(10, 30), max_orders=15),
        TimeSlot(label="10:30 AM - 11:00 AM", start_time=time(10, 30), end_time=time(11, 0),  max_orders=15),
        TimeSlot(label="11:00 AM - 11:30 AM", start_time=time(11, 0),  end_time=time(11, 30), max_orders=15),
        TimeSlot(label="11:30 AM - 12:00 PM", start_time=time(11, 30), end_time=time(12, 0),  max_orders=15),
    ]

    db.session.add_all(products)
    db.session.add_all(time_slots)
    db.session.commit()

    return jsonify({"message": "CHOCOPO menu and time slots added successfully."}), 201


# ─────────────────────────────────────────────
# PUBLIC – CATEGORIES & PRODUCTS
# ─────────────────────────────────────────────

@api.route("/categories", methods=["GET"])
def get_categories():
    categories = Category.query.filter_by(is_active=True).all()
    return jsonify([
        {"id": c.id, "name": c.name, "image_url": c.image_url}
        for c in categories
    ])


@api.route("/products", methods=["GET"])
def get_products():
    category_id = request.args.get("category_id", type=int)
    query = Product.query.filter_by(is_available=True)
    if category_id:
        query = query.filter_by(category_id=category_id)
    products = query.order_by(Product.id.desc()).all()
    return jsonify([
        {
            "id": p.id,
            "category_id": p.category_id,
            "category_name": p.category.name,
            "name": p.name,
            "description": p.description,
            "price": float(p.price),
            "discount_price": float(p.discount_price) if p.discount_price is not None else None,
            "offers": p.offers,
            "image_url": p.image_url,
            "preparation_minutes": p.preparation_minutes,
            "is_featured": p.is_featured
        }
        for p in products
    ])


@api.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    p = Product.query.get_or_404(product_id)
    return jsonify({
        "id": p.id,
        "category_id": p.category_id,
        "category_name": p.category.name,
        "name": p.name,
        "description": p.description,
        "price": float(p.price),
        "discount_price": float(p.discount_price) if p.discount_price is not None else None,
        "offers": p.offers,
        "image_url": p.image_url,
        "preparation_minutes": p.preparation_minutes,
        "is_available": p.is_available
    })


# ─────────────────────────────────────────────
# PUBLIC – TIME SLOTS
# ─────────────────────────────────────────────

@api.route("/time-slots", methods=["GET"])
def get_time_slots():
    selected_date_text = request.args.get("date")

    if not selected_date_text:
        return jsonify({"message": "Date is required. Use ?date=YYYY-MM-DD"}), 400

    try:
        selected_date = datetime.strptime(selected_date_text, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"message": "Invalid date format. Use YYYY-MM-DD"}), 400

    if selected_date < date.today():
        return jsonify({"message": "Past dates are not allowed."}), 400

    active_slots = TimeSlot.query.filter_by(is_active=True).order_by(TimeSlot.start_time.asc()).all()
    response = []

    for slot in active_slots:
        booked = Order.query.filter_by(
            scheduled_date=selected_date,
            time_slot_id=slot.id
        ).filter(Order.order_status.notin_(["cancelled", "rejected"])).count()

        response.append({
            "id": slot.id,
            "label": slot.label,
            "start_time": slot.start_time.strftime("%H:%M"),
            "end_time": slot.end_time.strftime("%H:%M"),
            "max_orders": slot.max_orders,
            "booked_orders": booked,
            "remaining_orders": max(slot.max_orders - booked, 0),
            "is_available": booked < slot.max_orders
        })

    return jsonify(response)


# ─────────────────────────────────────────────
# PUBLIC – ORDERS (create)
# ─────────────────────────────────────────────

@api.route("/orders", methods=["POST"])
def create_order():
    data = request.get_json() or {}

    full_name        = str(data.get("full_name", "")).strip()
    phone            = str(data.get("phone", "")).strip()
    email            = str(data.get("email", "")).strip() or None
    order_type       = str(data.get("order_type", "pickup")).strip().lower()
    delivery_address = str(data.get("delivery_address", "")).strip() or None
    scheduled_date_text = str(data.get("scheduled_date", "")).strip()
    time_slot_id     = data.get("time_slot_id")
    notes            = str(data.get("notes", "")).strip() or None
    payment_method   = str(data.get("payment_method", "cash_on_pickup")).strip().lower()
    items            = data.get("items", [])

    if not full_name or not phone:
        return jsonify({"message": "Customer name and phone number are required."}), 400
    if order_type not in ["pickup", "delivery"]:
        return jsonify({"message": "Order type must be pickup or delivery."}), 400
    if order_type == "delivery" and not delivery_address:
        return jsonify({"message": "Delivery address is required for delivery orders."}), 400
    if payment_method not in ["cash_on_pickup", "online"]:
        return jsonify({"message": "Invalid payment method."}), 400
    if not isinstance(items, list) or len(items) == 0:
        return jsonify({"message": "Your cart is empty."}), 400

    try:
        selected_date = datetime.strptime(scheduled_date_text, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"message": "Invalid scheduled date. Use YYYY-MM-DD."}), 400

    if selected_date < date.today():
        return jsonify({"message": "Past dates are not allowed."}), 400

    try:
        time_slot_id = int(time_slot_id)
    except (TypeError, ValueError):
        return jsonify({"message": "Please select a valid time slot."}), 400

    time_slot = TimeSlot.query.filter_by(id=time_slot_id, is_active=True).first()
    if not time_slot:
        return jsonify({"message": "Selected time slot is not available."}), 400

    booked = Order.query.filter_by(
        scheduled_date=selected_date,
        time_slot_id=time_slot.id
    ).filter(Order.order_status.notin_(["cancelled", "rejected"])).count()

    if booked >= time_slot.max_orders:
        return jsonify({"message": "This time slot is already full. Please choose another one."}), 400

    now = datetime.now()
    if selected_date == date.today():
        slot_datetime = datetime.combine(selected_date, time_slot.start_time)
        if slot_datetime <= now + timedelta(minutes=15):
            return jsonify({"message": "Please choose a pickup time at least 15 minutes from now."}), 400

    validated_items = []
    subtotal = Decimal("0.00")

    for item in items:
        try:
            product_id = int(item.get("product_id"))
            quantity   = int(item.get("quantity"))
        except (TypeError, ValueError):
            return jsonify({"message": "Invalid item in cart."}), 400

        if quantity < 1 or quantity > 20:
            return jsonify({"message": "Item quantity must be between 1 and 20."}), 400

        product = Product.query.filter_by(id=product_id, is_available=True).first()
        if not product:
            return jsonify({"message": "One of the selected products is unavailable."}), 400

        actual_price = product.discount_price if product.discount_price is not None else product.price
        item_total   = Decimal(str(actual_price)) * quantity
        subtotal    += item_total
        validated_items.append({"product": product, "quantity": quantity, "actual_price": actual_price, "item_total": item_total})

    delivery_fee = Decimal("40.00") if order_type == "delivery" else Decimal("0.00")
    total_amount = subtotal + delivery_fee

    customer = Customer.query.filter_by(phone=phone).first()
    if customer:
        customer.full_name = full_name
        customer.email = email or customer.email
    else:
        customer = Customer(full_name=full_name, phone=phone, email=email)
        db.session.add(customer)
        db.session.flush()

    order_number = f"CHO-{datetime.now().strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}"
    order = Order(
        order_number=order_number,
        customer_id=customer.id,
        order_type=order_type,
        scheduled_date=selected_date,
        time_slot_id=time_slot.id,
        delivery_address=delivery_address,
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        total_amount=total_amount,
        order_status="pending",
        payment_method=payment_method,
        payment_status="pending",
        notes=notes
    )
    db.session.add(order)
    db.session.flush()

    for item in validated_items:
        db.session.add(OrderItem(
            order_id=order.id,
            product_id=item["product"].id,
            product_name=item["product"].name,
            unit_price=item["actual_price"],
            quantity=item["quantity"],
            total_price=item["item_total"]
        ))

    db.session.commit()

    return jsonify({
        "message": "Your CHOCOPO order has been placed successfully.",
        "order": {
            "id": order.id,
            "order_number": order.order_number,
            "customer_name": customer.full_name,
            "phone": customer.phone,
            "order_type": order.order_type,
            "scheduled_date": order.scheduled_date.isoformat(),
            "time_slot": time_slot.label,
            "total_amount": float(order.total_amount),
            "order_status": order.order_status,
            "payment_method": order.payment_method,
            "payment_status": order.payment_status
        }
    }), 201


# ─────────────────────────────────────────────
# RAZORPAY – STEP 1: CREATE PAYMENT ORDER
# Validates all order data, creates a Razorpay
# order and returns the order_id for the JS SDK.
# ─────────────────────────────────────────────

@api.route("/payment/create-order", methods=["POST"])
def payment_create_order():
    data = request.get_json() or {}

    full_name           = str(data.get("full_name", "")).strip()
    phone               = str(data.get("phone", "")).strip()
    email               = str(data.get("email", "")).strip() or None
    order_type          = str(data.get("order_type", "pickup")).strip().lower()
    delivery_address    = str(data.get("delivery_address", "")).strip() or None
    scheduled_date_text = str(data.get("scheduled_date", "")).strip()
    time_slot_id        = data.get("time_slot_id")
    notes               = str(data.get("notes", "")).strip() or None
    items               = data.get("items", [])

    # ── Basic validation ──────────────────────
    if not full_name or not phone:
        return jsonify({"message": "Customer name and phone number are required."}), 400
    if order_type not in ["pickup", "delivery"]:
        return jsonify({"message": "Order type must be pickup or delivery."}), 400
    if order_type == "delivery" and not delivery_address:
        return jsonify({"message": "Delivery address is required for delivery orders."}), 400
    if not isinstance(items, list) or len(items) == 0:
        return jsonify({"message": "Your cart is empty."}), 400

    # ── Date & slot validation ────────────────
    try:
        selected_date = datetime.strptime(scheduled_date_text, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"message": "Invalid scheduled date. Use YYYY-MM-DD."}), 400

    if selected_date < date.today():
        return jsonify({"message": "Past dates are not allowed."}), 400

    try:
        time_slot_id = int(time_slot_id)
    except (TypeError, ValueError):
        return jsonify({"message": "Please select a valid time slot."}), 400

    time_slot = TimeSlot.query.filter_by(id=time_slot_id, is_active=True).first()
    if not time_slot:
        return jsonify({"message": "Selected time slot is not available."}), 400

    booked = Order.query.filter_by(
        scheduled_date=selected_date,
        time_slot_id=time_slot.id
    ).filter(Order.order_status.notin_(["cancelled", "rejected"])).count()

    if booked >= time_slot.max_orders:
        return jsonify({"message": "This time slot is already full. Please choose another one."}), 400

    now = datetime.now()
    if selected_date == date.today():
        slot_datetime = datetime.combine(selected_date, time_slot.start_time)
        if slot_datetime <= now + timedelta(minutes=15):
            return jsonify({"message": "Please choose a pickup time at least 15 minutes from now."}), 400

    # ── Compute total ─────────────────────────
    subtotal = Decimal("0.00")
    for item in items:
        try:
            product_id = int(item.get("product_id"))
            quantity   = int(item.get("quantity"))
        except (TypeError, ValueError):
            return jsonify({"message": "Invalid item in cart."}), 400

        if quantity < 1 or quantity > 20:
            return jsonify({"message": "Item quantity must be between 1 and 20."}), 400

        product = Product.query.filter_by(id=product_id, is_available=True).first()
        if not product:
            return jsonify({"message": "One of the selected products is unavailable."}), 400

        actual_price = product.discount_price if product.discount_price is not None else product.price
        subtotal    += Decimal(str(actual_price)) * quantity

    delivery_fee = Decimal("40.00") if order_type == "delivery" else Decimal("0.00")
    total_amount = subtotal + delivery_fee

    # ── Create Razorpay order ─────────────────
    amount_paise = int(total_amount * 100)   # Razorpay uses smallest currency unit
    receipt      = f"chocopo_{uuid4().hex[:10]}"

    try:
        rz_order = razorpay_client.order.create({
            "amount":   amount_paise,
            "currency": "INR",
            "receipt":  receipt,
            "payment_capture": 1
        })
    except Exception as exc:
        return jsonify({"message": f"Could not create payment order: {exc}"}), 500

    return jsonify({
        "razorpay_order_id": rz_order["id"],
        "amount":            amount_paise,
        "currency":          "INR",
        "key":               RAZORPAY_KEY_ID,
        "receipt":           receipt
    }), 200


# ─────────────────────────────────────────────
# RAZORPAY – STEP 2: VERIFY PAYMENT & SAVE ORDER
# Called by frontend after a successful payment.
# ─────────────────────────────────────────────

@api.route("/payment/verify", methods=["POST"])
def payment_verify():
    data = request.get_json() or {}

    razorpay_order_id   = str(data.get("razorpay_order_id",   "")).strip()
    razorpay_payment_id = str(data.get("razorpay_payment_id", "")).strip()
    razorpay_signature  = str(data.get("razorpay_signature",  "")).strip()

    # ── Verify HMAC signature ─────────────────
    try:
        razorpay_client.utility.verify_payment_signature({
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        })
    except razorpay.errors.SignatureVerificationError:
        return jsonify({"message": "Payment verification failed. Signature mismatch."}), 400

    # ── Re-read order details from payload ────
    full_name           = str(data.get("full_name", "")).strip()
    phone               = str(data.get("phone", "")).strip()
    email               = str(data.get("email", "")).strip() or None
    order_type          = str(data.get("order_type", "pickup")).strip().lower()
    delivery_address    = str(data.get("delivery_address", "")).strip() or None
    scheduled_date_text = str(data.get("scheduled_date", "")).strip()
    time_slot_id        = data.get("time_slot_id")
    notes               = str(data.get("notes", "")).strip() or None
    items               = data.get("items", [])

    try:
        selected_date = datetime.strptime(scheduled_date_text, "%Y-%m-%d").date()
        time_slot_id  = int(time_slot_id)
    except (ValueError, TypeError):
        return jsonify({"message": "Invalid order data after payment."}), 400

    time_slot = TimeSlot.query.filter_by(id=time_slot_id, is_active=True).first()
    if not time_slot:
        return jsonify({"message": "Time slot no longer available."}), 400

    # ── Re-validate items & compute totals ────
    validated_items = []
    subtotal = Decimal("0.00")

    for item in items:
        product_id   = int(item.get("product_id"))
        quantity     = int(item.get("quantity"))
        product      = Product.query.filter_by(id=product_id, is_available=True).first()
        if not product:
            return jsonify({"message": "A product became unavailable."}), 400
        actual_price = product.discount_price if product.discount_price is not None else product.price
        item_total   = Decimal(str(actual_price)) * quantity
        subtotal    += item_total
        validated_items.append({"product": product, "quantity": quantity,
                                 "actual_price": actual_price, "item_total": item_total})

    delivery_fee = Decimal("40.00") if order_type == "delivery" else Decimal("0.00")
    total_amount = subtotal + delivery_fee

    # ── Upsert customer ───────────────────────
    customer = Customer.query.filter_by(phone=phone).first()
    if customer:
        customer.full_name = full_name
        customer.email     = email or customer.email
    else:
        customer = Customer(full_name=full_name, phone=phone, email=email)
        db.session.add(customer)
        db.session.flush()

    # ── Save confirmed order ──────────────────
    order_number = f"CHO-{datetime.now().strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}"
    order = Order(
        order_number=order_number,
        customer_id=customer.id,
        order_type=order_type,
        scheduled_date=selected_date,
        time_slot_id=time_slot.id,
        delivery_address=delivery_address,
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        total_amount=total_amount,
        order_status="pending",
        payment_method="online",
        payment_status="paid",
        notes=notes
    )
    db.session.add(order)
    db.session.flush()

    for item in validated_items:
        db.session.add(OrderItem(
            order_id=order.id,
            product_id=item["product"].id,
            product_name=item["product"].name,
            unit_price=item["actual_price"],
            quantity=item["quantity"],
            total_price=item["item_total"]
        ))

    db.session.commit()

    return jsonify({
        "message": "Payment verified. Your CHOCOPO order has been placed!",
        "order": {
            "id":             order.id,
            "order_number":   order.order_number,
            "customer_name":  customer.full_name,
            "phone":          customer.phone,
            "order_type":     order.order_type,
            "scheduled_date": order.scheduled_date.isoformat(),
            "time_slot":      time_slot.label,
            "total_amount":   float(order.total_amount),
            "order_status":   order.order_status,
            "payment_method": order.payment_method,
            "payment_status": order.payment_status,
            "razorpay_payment_id": razorpay_payment_id
        }
    }), 201


# ─────────────────────────────────────────────
# ADMIN AUTH
# ─────────────────────────────────────────────

@api.route("/admin/create-first-admin", methods=["POST"])
def create_first_admin():
    if Admin.query.first():
        return jsonify({"message": "An admin account already exists."}), 400

    data      = request.get_json() or {}
    full_name = str(data.get("full_name", "")).strip()
    email     = str(data.get("email", "")).strip().lower()
    password  = str(data.get("password", "")).strip()

    if not full_name or not email or not password:
        return jsonify({"message": "Full name, email, and password are required."}), 400
    if len(password) < 8:
        return jsonify({"message": "Password must contain at least 8 characters."}), 400

    admin = Admin(full_name=full_name, email=email)
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()

    return jsonify({"message": "First CHOCOPO admin account created successfully."}), 201


@api.route("/admin/login", methods=["POST"])
def admin_login():
    data     = request.get_json() or {}
    email    = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", "")).strip()

    admin = Admin.query.filter_by(email=email, is_active=True).first()

    if not admin or not admin.check_password(password):
        return jsonify({"message": "Invalid admin email or password."}), 401

    # identity must be a string for Flask-JWT-Extended v4+
    access_token = create_access_token(identity=admin.email)

    return jsonify({
        "message": "Admin login successful.",
        "access_token": access_token,
        "admin": {
            "id": admin.id,
            "full_name": admin.full_name,
            "email": admin.email
        }
    })


# ─────────────────────────────────────────────
# ADMIN – ORDERS
# ─────────────────────────────────────────────

@api.route("/admin/orders", methods=["GET"])
@jwt_required()
def admin_get_orders():
    selected_date_text = request.args.get("date")
    status = request.args.get("status") or request.args.get("order_status")

    query = Order.query.order_by(Order.scheduled_date.asc(), Order.created_at.desc())

    if selected_date_text:
        try:
            selected_date = datetime.strptime(selected_date_text, "%Y-%m-%d").date()
            query = query.filter_by(scheduled_date=selected_date)
        except ValueError:
            return jsonify({"message": "Invalid date format. Use YYYY-MM-DD."}), 400

    if status:
        query = query.filter_by(order_status=status)

    orders = query.all()
    return jsonify([serialize_order(o) for o in orders])


@api.route("/admin/orders/<int:order_id>/status", methods=["PUT"])
@jwt_required()
def admin_update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    data  = request.get_json() or {}

    new_status = str(data.get("order_status", data.get("status", ""))).strip().lower()

    allowed = ["pending", "accepted", "preparing", "ready", "completed", "cancelled", "rejected"]
    if new_status not in allowed:
        return jsonify({"message": "Invalid order status."}), 400

    order.order_status = new_status
    db.session.commit()

    return jsonify({
        "message": "Order status updated successfully.",
        "order_id": order.id,
        "order_status": order.order_status,
        "status": order.order_status
    })


# ─────────────────────────────────────────────
# ADMIN – CATEGORIES
# ─────────────────────────────────────────────

@api.route("/admin/categories", methods=["GET"])
@jwt_required()
def admin_get_categories():
    categories = Category.query.order_by(Category.id.asc()).all()
    return jsonify([
        {
            "id": c.id,
            "name": c.name,
            "image_url": c.image_url,
            "is_active": c.is_active,
            "product_count": Product.query.filter_by(category_id=c.id).count()
        }
        for c in categories
    ])


@api.route("/admin/categories", methods=["POST"])
@jwt_required()
def admin_create_category():
    data      = request.get_json() or {}
    name      = str(data.get("name", "")).strip()
    image_url = str(data.get("image_url", "")).strip() or None
    is_active = data.get("is_active", True)

    if not name:
        return jsonify({"message": "Category name is required."}), 400
    if Category.query.filter_by(name=name).first():
        return jsonify({"message": "Category with this name already exists."}), 400

    category = Category(name=name, image_url=image_url, is_active=is_active)
    db.session.add(category)
    db.session.commit()

    return jsonify({"message": "Category created successfully", "category_id": category.id}), 201


@api.route("/admin/categories/<int:category_id>", methods=["PUT"])
@jwt_required()
def admin_update_category(category_id):
    category = Category.query.get_or_404(category_id)
    data     = request.get_json() or {}

    if "name" in data:
        name     = str(data["name"]).strip()
        existing = Category.query.filter_by(name=name).first()
        if existing and existing.id != category_id:
            return jsonify({"message": "Category with this name already exists."}), 400
        category.name = name
    if "image_url" in data:
        category.image_url = str(data.get("image_url", "")).strip() or None
    if "is_active" in data:
        category.is_active = data["is_active"]

    db.session.commit()
    return jsonify({"message": "Category updated successfully"})


@api.route("/admin/categories/<int:category_id>", methods=["DELETE"])
@jwt_required()
def admin_delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    if Product.query.filter_by(category_id=category_id).first():
        return jsonify({"message": "Cannot delete category with associated products. Remove or reassign products first."}), 400
    db.session.delete(category)
    db.session.commit()
    return jsonify({"message": "Category deleted successfully"})


# ─────────────────────────────────────────────
# ADMIN – PRODUCTS
# ─────────────────────────────────────────────

@api.route("/admin/products", methods=["POST"])
@jwt_required()
def admin_create_product():
    data                = request.get_json() or {}
    category_id         = data.get("category_id")
    name                = str(data.get("name", "")).strip()
    description         = str(data.get("description", "")).strip() or None
    price               = data.get("price")
    discount_price      = data.get("discount_price")
    offers              = str(data.get("offers", "")).strip() or None
    image_url           = str(data.get("image_url", "")).strip() or None
    preparation_minutes = data.get("preparation_minutes", 15)
    is_available        = data.get("is_available", True)
    is_featured         = data.get("is_featured", False)

    if not name or not price or not category_id:
        return jsonify({"message": "Name, price, and category are required."}), 400

    product = Product(
        category_id=category_id,
        name=name,
        description=description,
        price=price,
        discount_price=discount_price,
        offers=offers,
        image_url=image_url,
        preparation_minutes=preparation_minutes,
        is_available=is_available,
        is_featured=is_featured
    )
    db.session.add(product)
    db.session.commit()

    return jsonify({"message": "Product created successfully", "product_id": product.id}), 201


@api.route("/admin/products/<int:product_id>", methods=["PUT"])
@jwt_required()
def admin_update_product(product_id):
    product = Product.query.get_or_404(product_id)
    data    = request.get_json() or {}

    if "category_id"         in data: product.category_id         = data["category_id"]
    if "name"                in data: product.name                = str(data["name"]).strip()
    if "description"         in data: product.description         = str(data["description"]).strip() or None
    if "price"               in data: product.price               = data["price"]
    if "discount_price"      in data: product.discount_price      = data.get("discount_price")
    if "offers"              in data: product.offers              = str(data.get("offers", "")).strip() or None
    if "image_url"           in data: product.image_url           = str(data.get("image_url", "")).strip() or None
    if "preparation_minutes" in data: product.preparation_minutes = data["preparation_minutes"]
    if "is_available"        in data: product.is_available        = data["is_available"]
    if "is_featured"         in data: product.is_featured         = data["is_featured"]

    db.session.commit()
    return jsonify({"message": "Product updated successfully"})


@api.route("/admin/products/<int:product_id>", methods=["DELETE"])
@jwt_required()
def admin_delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Product deleted successfully"})


# ─────────────────────────────────────────────
# PUBLIC – FRANCHISE
# ─────────────────────────────────────────────

@api.route("/franchise-enquiries", methods=["POST"])
def create_franchise_enquiry():
    data       = request.get_json() or {}
    full_name  = str(data.get("full_name", "")).strip()
    email      = str(data.get("email", "")).strip().lower()
    phone      = str(data.get("phone", "")).strip()
    city       = str(data.get("city", "")).strip()
    investment = str(data.get("investment", "")).strip()
    message    = str(data.get("message", "")).strip() or None

    if not full_name or not email or not phone or not city or not investment:
        return jsonify({"message": "Please fill in all required franchise enquiry fields."}), 400

    enquiry = FranchiseEnquiry(
        full_name=full_name, email=email, phone=phone,
        city=city, investment=investment, message=message, status="new"
    )
    db.session.add(enquiry)
    db.session.commit()

    return jsonify({"message": "Your franchise enquiry has been submitted successfully.", "enquiry_id": enquiry.id}), 201


@api.route("/admin/franchise-enquiries", methods=["GET"])
@jwt_required()
def admin_get_franchise_enquiries():
    enquiries = FranchiseEnquiry.query.order_by(FranchiseEnquiry.created_at.desc()).all()
    return jsonify([
        {
            "id": e.id, "full_name": e.full_name, "email": e.email,
            "phone": e.phone, "city": e.city, "investment": e.investment,
            "message": e.message, "status": e.status,
            "created_at": e.created_at.isoformat()
        }
        for e in enquiries
    ])


@api.route("/admin/franchise-enquiries/<int:enquiry_id>", methods=["PUT"])
@jwt_required()
def admin_update_franchise_enquiry(enquiry_id):
    enquiry = FranchiseEnquiry.query.get_or_404(enquiry_id)
    data    = request.get_json() or {}
    status  = str(data.get("status", "")).strip().lower()

    allowed = ["new", "contacted", "interested", "rejected"]
    if status and status in allowed:
        enquiry.status = status

    db.session.commit()
    return jsonify({"message": "Franchise enquiry updated."})


# ─────────────────────────────────────────────
# SUPPORT CHAT
# ─────────────────────────────────────────────

@api.route("/support/messages", methods=["GET"])
def get_support_messages():
    customer_name  = request.args.get("customer_name", "")
    customer_email = request.args.get("customer_email", "")

    query = SupportMessage.query
    if customer_email:
        query = query.filter_by(customer_email=customer_email)
    elif customer_name:
        query = query.filter_by(customer_name=customer_name)

    messages = query.order_by(SupportMessage.created_at.asc()).all()
    return jsonify([
        {
            "id": m.id, "customer_name": m.customer_name,
            "customer_email": m.customer_email, "message": m.message,
            "sender": m.sender, "is_read": m.is_read,
            "created_at": m.created_at.isoformat()
        }
        for m in messages
    ])


@api.route("/support/messages", methods=["POST"])
def send_support_message():
    data           = request.get_json() or {}
    customer_name  = str(data.get("customer_name", "")).strip() or None
    customer_email = str(data.get("customer_email", "")).strip() or None
    message        = str(data.get("message", "")).strip()
    sender         = str(data.get("sender", "customer")).strip()

    if not message:
        return jsonify({"message": "Message cannot be empty."}), 400

    msg = SupportMessage(
        customer_name=customer_name,
        customer_email=customer_email,
        message=message,
        sender=sender
    )
    db.session.add(msg)
    db.session.commit()

    return jsonify({"message": "Message sent.", "id": msg.id}), 201


@api.route("/admin/support-messages", methods=["GET"])
@jwt_required()
def admin_get_support_messages():
    messages = SupportMessage.query.order_by(SupportMessage.created_at.desc()).all()
    return jsonify([
        {
            "id": m.id, "customer_name": m.customer_name,
            "customer_email": m.customer_email, "message": m.message,
            "sender": m.sender, "is_read": m.is_read,
            "created_at": m.created_at.isoformat()
        }
        for m in messages
    ])


@api.route("/admin/support-messages/<int:message_id>/reply", methods=["POST"])
@jwt_required()
def admin_reply_support_message(message_id):
    original = SupportMessage.query.get_or_404(message_id)
    data     = request.get_json() or {}
    message  = str(data.get("message", "")).strip()

    if not message:
        return jsonify({"message": "Reply message cannot be empty."}), 400

    reply = SupportMessage(
        customer_name=original.customer_name,
        customer_email=original.customer_email,
        message=message,
        sender="admin"
    )
    original.is_read = True
    db.session.add(reply)
    db.session.commit()

    return jsonify({"message": "Reply sent.", "id": reply.id}), 201


# ─────────────────────────────────────────────
# CUSTOMER AUTH
# ─────────────────────────────────────────────

@api.route("/auth/register", methods=["POST"])
def register_customer():
    data      = request.get_json() or {}
    full_name = str(data.get("full_name", "")).strip()
    phone     = str(data.get("phone", "")).strip()
    email     = str(data.get("email", "")).strip().lower() or None
    password  = str(data.get("password", "")).strip()

    if not full_name or not phone or not password:
        return jsonify({"message": "Full name, phone, and password are required."}), 400
    if len(password) < 6:
        return jsonify({"message": "Password must be at least 6 characters."}), 400
    if Customer.query.filter_by(phone=phone).first():
        return jsonify({"message": "An account with this phone number already exists."}), 400

    customer = Customer(full_name=full_name, phone=phone, email=email)
    customer.set_password(password)
    db.session.add(customer)
    db.session.commit()

    token = create_access_token(identity=str(customer.id))
    return jsonify({
        "message": "Account created successfully.",
        "access_token": token,
        "customer": {"id": customer.id, "full_name": customer.full_name, "phone": customer.phone, "email": customer.email}
    }), 201


@api.route("/auth/login", methods=["POST"])
def login_customer():
    data     = request.get_json() or {}
    phone    = str(data.get("phone", "")).strip()
    password = str(data.get("password", "")).strip()

    if not phone or not password:
        return jsonify({"message": "Phone and password are required."}), 400

    customer = Customer.query.filter_by(phone=phone).first()
    if not customer or not customer.check_password(password):
        return jsonify({"message": "Invalid phone number or password."}), 401

    token = create_access_token(identity=str(customer.id))
    return jsonify({
        "message": "Login successful.",
        "access_token": token,
        "customer": {"id": customer.id, "full_name": customer.full_name, "phone": customer.phone, "email": customer.email}
    })


@api.route("/auth/profile", methods=["GET"])
@jwt_required()
def get_profile():
    identity    = get_jwt_identity()
    customer_id = int(identity)
    customer    = Customer.query.get_or_404(customer_id)
    return jsonify({"id": customer.id, "full_name": customer.full_name, "phone": customer.phone, "email": customer.email})


@api.route("/auth/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    identity    = get_jwt_identity()
    customer_id = int(identity)
    customer    = Customer.query.get_or_404(customer_id)
    data        = request.get_json() or {}

    if "full_name" in data: customer.full_name = str(data["full_name"]).strip()
    if "email"     in data: customer.email     = str(data["email"]).strip().lower() or None

    db.session.commit()
    return jsonify({"message": "Profile updated.", "customer": {"id": customer.id, "full_name": customer.full_name, "phone": customer.phone, "email": customer.email}})


@api.route("/my-orders", methods=["GET"])
@jwt_required()
def get_my_orders():
    identity    = get_jwt_identity()
    customer_id = int(identity)
    orders      = Order.query.filter_by(customer_id=customer_id).order_by(Order.created_at.desc()).all()
    return jsonify([serialize_order(o) for o in orders])


@api.route("/my-orders/<int:order_id>/cancel", methods=["PUT"])
@jwt_required()
def cancel_my_order(order_id):
    identity    = get_jwt_identity()
    customer_id = int(identity)
    order       = Order.query.filter_by(id=order_id, customer_id=customer_id).first_or_404()
    if order.order_status not in ["pending", "confirmed"]:
        return jsonify({"message": "Order cannot be cancelled at this stage."}), 400
    order.order_status = "cancelled"
    db.session.commit()
    return jsonify({"message": "Order cancelled."})
