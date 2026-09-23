import os
import sqlite3
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash
from flask import Flask, jsonify, render_template, request, session

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "khetsetu.db")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "khetsetu-development-key")


def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def seed_database():
    connection = get_db()
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS farmers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            village TEXT NOT NULL,
            state TEXT NOT NULL,
            land_acres REAL NOT NULL,
            irrigation TEXT NOT NULL,
            soil TEXT NOT NULL,
            verified INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('farmer', 'retailer')),
            farmer_id INTEGER,
            business_name TEXT,
            location TEXT,
            verified INTEGER DEFAULT 1,
            FOREIGN KEY (farmer_id) REFERENCES farmers(id)
        );
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_id INTEGER NOT NULL,
            crop TEXT NOT NULL,
            grade TEXT NOT NULL,
            quantity_kg INTEGER NOT NULL,
            price_per_kg REAL NOT NULL,
            available_date TEXT NOT NULL,
            status TEXT DEFAULT 'available',
            FOREIGN KEY (farmer_id) REFERENCES farmers(id)
        );
        CREATE TABLE IF NOT EXISTS demands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            buyer_name TEXT NOT NULL,
            location TEXT NOT NULL,
            crop TEXT NOT NULL,
            quantity_kg INTEGER NOT NULL,
            grade TEXT NOT NULL,
            needed_by TEXT NOT NULL,
            price_per_kg REAL NOT NULL,
            status TEXT DEFAULT 'open'
        );
        CREATE TABLE IF NOT EXISTS offers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            demand_id INTEGER NOT NULL,
            farmer_id INTEGER NOT NULL,
            price_per_kg REAL NOT NULL,
            quantity_kg INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (demand_id) REFERENCES demands(id),
            FOREIGN KEY (farmer_id) REFERENCES farmers(id)
        );
        """
    )
    if connection.execute("SELECT COUNT(*) FROM farmers").fetchone()[0] == 0:
        connection.executemany(
            "INSERT INTO farmers (name, village, state, land_acres, irrigation, soil) VALUES (?, ?, ?, ?, ?, ?)",
            [
                ("Superman", "Kondapur", "Telangana", 4.0, "Borewell", "Black soil"),
                ("Sujatha Devi", "Moinabad", "Telangana", 6.5, "Canal", "Red soil"),
                ("Venkatesh Rao", "Shamirpet", "Telangana", 3.0, "Rainfed", "Loamy soil"),
            ],
        )
    if connection.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        connection.execute(
            "INSERT INTO users (name, email, password_hash, role, farmer_id) VALUES (?, ?, ?, ?, ?)",
            ("Superman", "farmer@khetsetu.demo", generate_password_hash("farmer123"), "farmer", 1),
        )
        connection.execute(
            "INSERT INTO users (name, email, password_hash, role, business_name, location) VALUES (?, ?, ?, ?, ?, ?)",
            ("Ananya Mehta", "retailer@khetsetu.demo", generate_password_hash("retailer123"), "retailer", "FreshCart Retail", "Hyderabad"),
        )
        connection.executemany(
            "INSERT INTO listings (farmer_id, crop, grade, quantity_kg, price_per_kg, available_date) VALUES (?, ?, ?, ?, ?, ?)",
            [
                (1, "Tomato", "Grade A", 800, 28, "2026-09-27"),
                (2, "Green chilli", "Premium", 450, 76, "2026-09-29"),
                (3, "Groundnut", "Grade A", 1200, 68, "2026-10-04"),
            ],
        )
        connection.executemany(
            "INSERT INTO demands (buyer_name, location, crop, quantity_kg, grade, needed_by, price_per_kg) VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                ("FreshCart Retail", "Hyderabad", "Tomato", 2000, "Grade A", "2026-10-01", 30),
                ("Nizam Wholesale", "Secunderabad", "Green chilli", 1000, "Premium", "2026-10-03", 80),
                ("Daily Basket", "Gachibowli", "Groundnut", 1500, "Grade A", "2026-10-10", 70),
            ],
        )
    connection.commit()
    connection.close()


def rows_as_dict(rows):
    return [dict(row) for row in rows]


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    connection = get_db()
    user = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    connection.close()
    return dict(user) if user else None


def role_required(role):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = current_user()
            if not user:
                return jsonify({"error": "Please log in to continue."}), 401
            if user["role"] != role:
                return jsonify({"error": f"This action is only available to {role}s."}), 403
            return view(*args, **kwargs)
        return wrapped
    return decorator


@app.route("/")
def index():
    return render_template("index.html")


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/api/session")
def session_info():
    user = current_user()
    if not user:
        return jsonify({"authenticated": False})
    user.pop("password_hash", None)
    return jsonify({"authenticated": True, "user": user})


@app.post("/api/register")
def register():
    data = request.get_json() or {}
    required = ["name", "email", "password", "role"]
    if any(not str(data.get(field, "")).strip() for field in required):
        return jsonify({"error": "Name, email, password, and account type are required."}), 400
    role = data["role"]
    if role not in ("farmer", "retailer"):
        return jsonify({"error": "Choose farmer or retailer as your account type."}), 400
    connection = get_db()
    try:
        farmer_id = None
        if role == "farmer":
            cursor = connection.execute(
                "INSERT INTO farmers (name, village, state, land_acres, irrigation, soil) VALUES (?, ?, ?, ?, ?, ?)",
                (data["name"], data.get("village", "To be added"), data.get("state", "Telangana"), float(data.get("land_acres") or 0), data.get("irrigation", "To be added"), data.get("soil", "To be added")),
            )
            farmer_id = cursor.lastrowid
        cursor = connection.execute(
            "INSERT INTO users (name, email, password_hash, role, farmer_id, business_name, location) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (data["name"], data["email"].lower().strip(), generate_password_hash(data["password"]), role, farmer_id, data.get("business_name") or data["name"], data.get("location", "Hyderabad")),
        )
        connection.commit()
        session["user_id"] = cursor.lastrowid
    except sqlite3.IntegrityError:
        connection.rollback()
        return jsonify({"error": "An account with this email already exists."}), 409
    finally:
        connection.close()
    return jsonify({"message": "Account created", "role": role}), 201


@app.post("/api/login")
def login():
    data = request.get_json() or {}
    email = str(data.get("email", "")).lower().strip()
    password = str(data.get("password", ""))
    connection = get_db()
    user = connection.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    connection.close()
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Email or password is incorrect."}), 401
    session["user_id"] = user["id"]
    return jsonify({"message": "Logged in", "role": user["role"]})


@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})


@app.get("/api/dashboard")
@role_required("farmer")
def dashboard():
    user = current_user()
    connection = get_db()
    farmer = connection.execute("SELECT * FROM farmers WHERE id = ?", (user["farmer_id"],)).fetchone()
    listings = connection.execute(
        "SELECT listings.*, farmers.name, farmers.village FROM listings JOIN farmers ON farmers.id = listings.farmer_id WHERE listings.farmer_id = ? AND listings.status = 'available' ORDER BY listings.id", (user["farmer_id"],)
    ).fetchall()
    demands = connection.execute("SELECT * FROM demands WHERE status = 'open' ORDER BY needed_by").fetchall()
    connection.close()
    return jsonify({
        "user": user,
        "farmer": dict(farmer),
        "listings": rows_as_dict(listings),
        "demands": rows_as_dict(demands),
        "stats": {"active_buyers": 18, "matched_orders": 7, "avg_price_change": 12},
        "recommendations": [
            {"crop": "Groundnut", "demand": "High", "price": "₹68–72/kg", "reason": "Strong buyer demand nearby and suitable for black soil."},
            {"crop": "Green chilli", "demand": "High", "price": "₹72–84/kg", "reason": "4 buyers need premium lots before 3 October."},
            {"crop": "Tomato", "demand": "Steady", "price": "₹26–31/kg", "reason": "Harvest window aligns with weekly retail demand."},
        ],
    })


@app.get("/api/retailer/dashboard")
@role_required("retailer")
def retailer_dashboard():
    user = current_user()
    connection = get_db()
    listings = connection.execute(
        "SELECT listings.*, farmers.name, farmers.village FROM listings JOIN farmers ON farmers.id = listings.farmer_id WHERE listings.status = 'available' ORDER BY listings.available_date"
    ).fetchall()
    demands = connection.execute("SELECT * FROM demands WHERE buyer_name = ? ORDER BY needed_by", (user["business_name"],)).fetchall()
    offers = connection.execute(
        "SELECT offers.*, demands.crop, farmers.name AS farmer_name FROM offers JOIN demands ON demands.id = offers.demand_id JOIN farmers ON farmers.id = offers.farmer_id WHERE demands.buyer_name = ? ORDER BY offers.id DESC", (user["business_name"],)
    ).fetchall()
    connection.close()
    return jsonify({"user": user, "listings": rows_as_dict(listings), "demands": rows_as_dict(demands), "offers": rows_as_dict(offers), "stats": {"available_lots": len(listings), "active_requests": len(demands), "offers_received": len(offers)}})


@app.post("/api/demands")
@role_required("retailer")
def create_demand():
    user = current_user()
    data = request.get_json() or {}
    required = ["location", "crop", "quantity_kg", "grade", "needed_by", "price_per_kg"]
    if any(not data.get(field) for field in required):
        return jsonify({"error": "Please complete every requirement field."}), 400
    connection = get_db()
    cursor = connection.execute(
        "INSERT INTO demands (buyer_name, location, crop, quantity_kg, grade, needed_by, price_per_kg) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user["business_name"], data["location"], data["crop"], data["quantity_kg"], data["grade"], data["needed_by"], data["price_per_kg"]),
    )
    connection.commit()
    demand = connection.execute("SELECT * FROM demands WHERE id = ?", (cursor.lastrowid,)).fetchone()
    connection.close()
    return jsonify(dict(demand)), 201


@app.post("/api/listings")
@role_required("farmer")
def create_listing():
    user = current_user()
    data = request.get_json() or {}
    required = ["crop", "grade", "quantity_kg", "price_per_kg", "available_date"]
    if any(not data.get(field) for field in required):
        return jsonify({"error": "Please complete every produce field."}), 400
    connection = get_db()
    cursor = connection.execute(
        "INSERT INTO listings (farmer_id, crop, grade, quantity_kg, price_per_kg, available_date) VALUES (?, ?, ?, ?, ?, ?)",
        (user["farmer_id"], *(data[field] for field in required)),
    )
    connection.commit()
    listing = connection.execute("SELECT * FROM listings WHERE id = ?", (cursor.lastrowid,)).fetchone()
    connection.close()
    return jsonify(dict(listing)), 201


@app.post("/api/offers")
@role_required("farmer")
def create_offer():
    user = current_user()
    data = request.get_json() or {}
    required = ["demand_id", "quantity_kg", "price_per_kg"]
    if any(not data.get(field) for field in required):
        return jsonify({"error": "Please add quantity and your offer price."}), 400
    connection = get_db()
    connection.execute(
        "INSERT INTO offers (demand_id, farmer_id, quantity_kg, price_per_kg) VALUES (?, ?, ?, ?)",
        (data["demand_id"], user["farmer_id"], data["quantity_kg"], data["price_per_kg"]),
    )
    connection.commit()
    connection.close()
    return jsonify({"message": "Offer sent to the buyer."}), 201


seed_database()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
