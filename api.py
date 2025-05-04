from flask import Flask, request, jsonify
from flask_cors import CORS
import pyodbc
import bcrypt
import datetime

app = Flask(__name__)

# Allow CORS for frontend access
CORS(app, resources={r"/*": {"origins": "http://localhost:8000"}})

# SQL Server Configuration
app.config["SQL_SERVER"] = "localhost"
app.config["SQL_DATABASE"] = "Restaurant"

# Connection String
connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={app.config["SQL_SERVER"]};DATABASE={app.config["SQL_DATABASE"]};Trusted_Connection=yes;'

# **Create Account Route**
@app.route("/createacc", methods=["POST"])
def create_account():
    data = request.json
    first_name = data.get("firstName")
    last_name = data.get("lastName")
    address = data.get("address")
    phone_no = data.get("phoneNo")
    username = data.get("uname")
    password = data.get("psw")

    if not all([first_name, last_name, address, phone_no, username, password]):
        return jsonify({"message": "All fields are required"}), 400

    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()

        # Check if username already exists
        cursor.execute("SELECT username FROM login WHERE username = ?", (username,))
        existing_user = cursor.fetchone()
        if existing_user:
            return jsonify({"message": "Username already exists!"}), 400

        # Hash the password before storing
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        # Insert new user into the database
        cursor.execute("""
            INSERT INTO login (username, password, firstName, lastName, address, phoneNo)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (username, hashed_password.decode("utf-8"), first_name, last_name, address, phone_no))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "Account created successfully!"}), 201

    except Exception as e:
        return jsonify({"message": f"Error creating account: {str(e)}"}), 500


# **Login Route**
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("uname")
    password = data.get("psw")

    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        cursor.execute("SELECT userid, password FROM login WHERE username = ?", (username,))
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()

        if user:
            stored_password = user[1]

            # Verify hashed password
            if bcrypt.checkpw(password.encode("utf-8"), stored_password.encode("utf-8")):
                return jsonify({"message": "Login successful", "userid": user[0]}), 200
            else:
                return jsonify({"message": "Invalid password"}), 401
        else:
            return jsonify({"message": "Invalid username"}), 401

    except Exception as e:
        return jsonify({"message": f"Error connecting to database: {str(e)}"}), 500


# **Contact (Booking Request) Route**
@app.route("/contact", methods=["POST"])
def contact():
    data = request.json
    userid = data.get("userid")
    people_count = data.get("people_count")
    special_requirement = data.get("special_requirement")
    booking_time = data.get("booking_time")

    if not all([userid, people_count, special_requirement, booking_time]):
        return jsonify({"message": "All fields are required"}), 400

    try:
        booking_time = datetime.datetime.fromisoformat(booking_time)

        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()

        cursor.execute("SELECT userid FROM login WHERE userid = ?", (userid,))
        user = cursor.fetchone()
        if not user:
            return jsonify({"message": "Invalid userid"}), 400

        cursor.execute("""
            INSERT INTO contact_requests (userid, people_count, special_requirement, booking_time)
            VALUES (?, ?, ?, ?)
        """, (userid, people_count, special_requirement, booking_time))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "Booking request submitted successfully"}), 201

    except ValueError:
        return jsonify({"message": "Invalid datetime format"}), 400
    except Exception as e:
        return jsonify({"message": f"Error connecting to database: {str(e)}"}), 500


# **Order Placement Route**
@app.route("/place_order", methods=["POST"])
def place_order():
    data = request.json
    userid = data.get("userid")
    item_name = data.get("item_name")
    price = data.get("price")
    address = data.get("address")
    payment_method = data.get("payment_method")

    if not all([userid, item_name, price, address, payment_method]):
        return jsonify({"message": "All fields are required"}), 400

    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()

        cursor.execute("SELECT userid FROM login WHERE userid = ?", (userid,))
        user = cursor.fetchone()
        if not user:
            return jsonify({"message": "Invalid userid"}), 400

        cursor.execute("""
            INSERT INTO orders (userid, item_name, price, address, payment_method, order_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (userid, item_name, price, address, payment_method, datetime.datetime.now()))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "Order placed successfully"}), 201

    except Exception as e:
        return jsonify({"message": f"Error placing order: {str(e)}"}), 500


# **Run Flask App**
if __name__ == "__main__":
    app.run(debug=True, port=5000)
