from flask import Flask, request, jsonify,render_template
import snowflake.connector
import bcrypt

app = Flask(__name__)

# Snowflake connection
conn = snowflake.connector.connect(
    user='nithian',
    password='Abc2152005',
    account='pniwdtf-ya84570',
    warehouse='COMPUTE_WH',
    database='SRIK',
    schema='LOGIN'
)
@app.route('/')
def home():
    return render_template('login-2.html') 
@app.route('/register.html')
def register():
    return render_template('register.html')  # Render registration page

@app.route('/register', methods=['POST'])
def register1():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    employee_id = data.get('employee_id')  # Can be None if not an employee

    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    # Insert into Snowflake
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (name, email, password, employee_id)
            VALUES (%s, %s, %s, %s)
        """, (name, email, hashed_password.decode('utf-8'), employee_id))

        return jsonify({"message": "User registered successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT password FROM users WHERE email = %s
        """, (email,))
        result = cursor.fetchone()

        if result and bcrypt.checkpw(password.encode('utf-8'), result[0].encode('utf-8')):
            return jsonify({"message": "Login successful"}), 200
        else:
            return jsonify({"error": "Invalid email or password"}), 401

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()

if __name__ == '__main__':
    app.run(debug=True)
