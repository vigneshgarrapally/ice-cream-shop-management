from datetime import datetime, timedelta, date
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
)
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from flask_bcrypt import Bcrypt
from app import app, db, bcrypt, login_manager
from .models import User, Product, Order, OrderItem
from sqlalchemy import func, extract
from sqlalchemy.exc import SQLAlchemyError
import calendar


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("invoice"))
        else:
            flash("Invalid username or password", "danger")
    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        existing_user = User.query.filter_by(username=username).first()
        if existing_user is None:
            hashed_password = bcrypt.generate_password_hash(password).decode(
                "utf-8"
            )
            new_user = User(username=username, password_hash=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for("login"))
        flash("Username already exists")
    return render_template("signup.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/invoice", methods=["GET", "POST"])
def invoice():
    if request.method == "POST":
        # This part handles the POST request when the order is finalized
        items = request.json["items"]
        if not items:
            return (
                jsonify({"status": "error", "message": "No items provided"}),
                400,
            )
        try:
            new_order = Order(
                user_id=current_user.id,
                total_amount=0,
                gst_amount=0,
                final_amount=0,
                status="Pending",
            )
            db.session.add(new_order)
            db.session.flush()
            total_price = 0
            for item in items:
                product = Product.query.get(item["product_id"])
                if product and item["quantity"] > 0:
                    subtotal = product.price * item["quantity"]
                    order_item = OrderItem(
                        order=new_order,
                        product=product,
                        quantity=item["quantity"],
                        item_price=subtotal,
                    )
                    db.session.add(order_item)
                    total_price += subtotal
            if total_price == 0:
                db.session.rollback()
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": "Total price cannot be zero",
                        }
                    ),
                    400,
                )
            gst = total_price * 0.18  # Assuming 18% GST
            new_order.total_amount = total_price
            new_order.gst_amount = gst
            new_order.final_amount = total_price + gst

            db.session.commit()
            return jsonify({"status": "success", "order_id": new_order.id})
        except Exception as e:
            db.session.rollback()
            return jsonify({"status": "error", "message": str(e)}), 500
    try:
        # GET request will fetch the page initially and after order completion
        products = Product.query.all()
        return render_template("invoice.html", products=products)
    except SQLAlchemyError as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/history")
@login_required
def history():
    orders = (
        Order.query.filter_by(user_id=current_user.id)
        .order_by(Order.order_time.desc())
        .all()
    )
    return render_template("history.html", orders=orders)


@app.route("/analytics")
@login_required
def analytics():
    today = (
        date.today()
    )  # Ensure we're working with date only, removing time component
    start_of_week = today - timedelta(
        days=today.weekday()
    )  # Monday of this week
    start_of_month = today.replace(day=1)  # First day of the current month
    start_of_year = today.replace(month=1, day=1)

    daily_sales = (
        db.session.query(func.sum(Order.final_amount))
        .filter(func.date(Order.order_time) == today)
        .scalar()
        or 0
    )
    weekly_sales = (
        db.session.query(func.sum(Order.final_amount))
        .filter(func.date(Order.order_time) >= start_of_week)
        .scalar()
        or 0
    )
    monthly_sales = (
        db.session.query(func.sum(Order.final_amount))
        .filter(func.date(Order.order_time) >= start_of_month)
        .scalar()
        or 0
    )
    yearly_sales = (
        db.session.query(func.sum(Order.final_amount))
        .filter(func.date(Order.order_time) >= start_of_year)
        .scalar()
        or 0
    )

    # Round sales data to 2 decimal places for better presentation
    daily_sales = round(daily_sales, 2)
    weekly_sales = round(weekly_sales, 2)
    monthly_sales = round(monthly_sales, 2)
    yearly_sales = round(yearly_sales, 2)

    # Popular products
    popular_products = (
        db.session.query(
            Product.name, func.sum(OrderItem.quantity).label("total_sold")
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .group_by(Product.name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(5)
        .all()
    )

    # Monthly sales for the last 12 months
    monthly_sales_data = (
        db.session.query(
            extract("year", Order.order_time).label("year"),
            extract("month", Order.order_time).label("month"),
            func.sum(Order.final_amount).label("total"),
        )
        .filter(Order.order_time >= (today - timedelta(days=365)))
        .group_by(
            extract("year", Order.order_time),
            extract("month", Order.order_time),
        )
        .order_by(
            extract("year", Order.order_time),
            extract("month", Order.order_time),
        )
        .all()
    )

    monthly_sales_last_year = [
        (f"{calendar.month_name[month]} {year}", round(total, 2))
        for year, month, total in monthly_sales_data
    ]

    product_sales = (
        db.session.query(
            Product.name,
            func.sum(OrderItem.quantity * Product.price).label("total_sales"),
        )
        .join(OrderItem, Product.id == OrderItem.product_id)
        .group_by(Product.name)
        .all()
    )

    return render_template(
        "analytics.html",
        daily_sales=daily_sales,
        weekly_sales=weekly_sales,
        monthly_sales=monthly_sales,
        yearly_sales=yearly_sales,
        monthly_sales_last_year=monthly_sales_last_year,
        popular_products=popular_products,
        product_sales=product_sales,
    )
