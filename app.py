from functools import wraps
import os
from flask import Flask, render_template, redirect, request, url_for, session, jsonify
import pyrebase
from datetime import datetime, timedelta

# ================= FIREBASE CONFIG =================
config = {
  "apiKey": "AIzaSyBMvDlJPf56koQdhjdjFZNOEtiKYedzYXw",
  "authDomain": "attendipi-ccd4e.firebaseapp.com",
  "databaseURL": "https://attendipi-ccd4e-default-rtdb.firebaseio.com",
  "projectId": "attendipi-ccd4e",
  "storageBucket": "attendipi-ccd4e.firebasestorage.app",
  "messagingSenderId": "779432739488",
  "appId": "1:779432739488:web:c59608f80245e151833fc5"
}

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()
db = firebase.database()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ================= AUTH =================
def isAuthenticated(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "usr" not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ================= LOGIN =================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            session['usr'] = user['idToken']
            return redirect("/")
        except:
            return render_template("login.html", message="Wrong Credentials")
    return render_template("login.html")

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ================= HOME =================
@app.route("/")
@isAuthenticated
def index():

    employees = db.child("employees").get().val() or {}
    attendance_db = db.child("attendance").get().val() or {}

    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    daily_set = set()
    weekly_set = set()
    monthly_set = set()

    for date_str, employees_att in attendance_db.items():

        try:
            date_obj = datetime.strptime(
                date_str,
                "%Y-%m-%d"
            ).date()
        except:
            continue

        employee_ids = []

        # Firebase returned dictionary
        if isinstance(employees_att, dict):

            employee_ids = [
                str(emp_id)
                for emp_id in employees_att.keys()
            ]

        # Firebase returned list
        elif isinstance(employees_att, list):

            for index, item in enumerate(employees_att):

                if isinstance(item, dict):

                    employee_ids.append(str(index))

        else:
            continue

        for emp_id in employee_ids:

            # Daily
            if date_obj == today:
                daily_set.add(emp_id)

            # Weekly
            if week_start <= date_obj <= today:
                weekly_set.add(emp_id)

            # Monthly
            if date_obj >= month_start:
                monthly_set.add(emp_id)

    print("DAILY:", daily_set)
    print("WEEKLY:", weekly_set)
    print("MONTHLY:", monthly_set)

    return render_template(
        "index.html",
        daily_count=len(daily_set),
        weekly_count=len(weekly_set),
        monthly_count=len(monthly_set),
        registered_count=len(employees)
    )

@app.route("/attendance")
@isAuthenticated
def attendance():

    attendance_db = db.child("attendance").get().val() or {}
    employees_db = db.child("employees").get().val() or {}

    attendance_rows = []

    print("ATTENDANCE DATA:")
    print(attendance_db)

    for date, employees in attendance_db.items():

        # =====================
        # DICTIONARY FORMAT
        # =====================
        if isinstance(employees, dict):

            for emp_id, record in employees.items():

                if not isinstance(record, dict):
                    continue

                name = record.get("name", "Unknown")
                time_in = record.get("time_in")
                time_out = record.get("time_out")

                total_time = "-"

                if time_in and time_out:
                    try:
                        t1 = datetime.strptime(time_in, "%H:%M:%S")
                        t2 = datetime.strptime(time_out, "%H:%M:%S")

                        diff = t2 - t1
                        total_seconds = int(diff.total_seconds())

                        hours = total_seconds // 3600
                        minutes = (total_seconds % 3600) // 60
                        seconds = total_seconds % 60

                        total_time = (
                            f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                        )

                    except Exception as e:
                        print("Time Error:", e)

                emp_info = employees_db.get(str(emp_id), {})
                image_url = emp_info.get("image_url")

                try:
                    sort_time = datetime.strptime(
                        f"{date} {time_in or '00:00:00'}",
                        "%Y-%m-%d %H:%M:%S"
                    )
                except:
                    sort_time = datetime.min

                attendance_rows.append({
                    "emp_id": str(emp_id),
                    "date": date,
                    "time_in": time_in,
                    "time_out": time_out,
                    "total_time": total_time,
                    "name": name,
                    "image": image_url,
                    "sort_time": sort_time
                })

        # =====================
        # LIST FORMAT
        # =====================
        elif isinstance(employees, list):

            for index, record in enumerate(employees):

                if not isinstance(record, dict):
                    continue

                emp_id = str(index)

                name = record.get("name", "Unknown")
                time_in = record.get("time_in")
                time_out = record.get("time_out")

                total_time = "-"

                if time_in and time_out:
                    try:
                        t1 = datetime.strptime(time_in, "%H:%M:%S")
                        t2 = datetime.strptime(time_out, "%H:%M:%S")

                        diff = t2 - t1
                        total_seconds = int(diff.total_seconds())

                        hours = total_seconds // 3600
                        minutes = (total_seconds % 3600) // 60
                        seconds = total_seconds % 60

                        total_time = (
                            f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                        )

                    except Exception as e:
                        print("Time Error:", e)

                emp_info = employees_db.get(emp_id, {})
                image_url = emp_info.get("image_url")

                try:
                    sort_time = datetime.strptime(
                        f"{date} {time_in or '00:00:00'}",
                        "%Y-%m-%d %H:%M:%S"
                    )
                except:
                    sort_time = datetime.min

                attendance_rows.append({
                    "emp_id": emp_id,
                    "date": date,
                    "time_in": time_in,
                    "time_out": time_out,
                    "total_time": total_time,
                    "name": name,
                    "image": image_url,
                    "sort_time": sort_time
                })

    attendance_rows.sort(
        key=lambda x: x["sort_time"],
        reverse=True
    )

    print("TOTAL RECORDS:", len(attendance_rows))
    print(attendance_rows)

    return render_template(
        "attendance_monitoring.html",
        attendance_rows=attendance_rows
    )

@app.route("/delete_attendance/<emp_id>/<date>", methods=["POST"])
@isAuthenticated
def delete_attendance(emp_id, date):
    try:
        db.child("attendance").child(date).child(emp_id).remove()
    except Exception as e:
        print("Delete Error:", e)

    return redirect(url_for('attendance'))

# ================= USERS =================
@app.route("/users")
@isAuthenticated
def users():
    employees = db.child("employees").get().val() or {}
    return render_template("users.html", employees=employees)

@app.route("/update_user/<emp_id>", methods=["POST"])
@isAuthenticated
def update_user(emp_id):
    try:
        data = request.get_json()
        db.child("employees").child(emp_id).update({
            "name": data.get("name"),
            "email": data.get("email")
        })
        return jsonify({"success": True})
    except Exception as e:
        print(e)
        return jsonify({"success": False})

# ================= RUN =================
if __name__ == '__main__':
    app.run(debug=True)