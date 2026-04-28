# Import Modules
from flask import Flask, render_template, request, redirect, session, g
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "assignment13_secret_key"

# Database file
DATABASE = "hw13.db"


# Database connection
def get_db():
    db = getattr(g, "_database", None)

    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row

    return db


# Close database connection
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)

    if db is not None:
        db.close()


# Initialize database from schema.sql
def init_db():
    with app.app_context():
        db = get_db()

        with open("schema.sql", "r") as file:
            db.cursor().executescript(file.read())

        db.commit()


# Login check
def is_logged_in():
    return session.get("logged_in")


# Controller 1: Home Page
@app.route("/")
def index():
    if is_logged_in():
        return redirect("/dashboard")

    return redirect("/login")


# Controller 2: Login
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == "admin" and password == "password":
            session["logged_in"] = True
            return redirect("/dashboard")
        else:
            error = "Invalid username or password."

    return render_template("login.html", error=error)


# Controller 3: Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# Controller 4: Dashboard
@app.route("/dashboard")
def dashboard():
    if not is_logged_in():
        return redirect("/login")

    db = get_db()

    students = db.execute("SELECT * FROM students").fetchall()
    quizzes = db.execute("SELECT * FROM quizzes").fetchall()

    return render_template("dashboard.html", students=students, quizzes=quizzes)


# Controller 5: Add Student
@app.route("/student/add", methods=["GET", "POST"])
def add_student():
    if not is_logged_in():
        return redirect("/login")

    error = None

    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")

        if not first_name or not last_name:
            error = "First name and last name are required."
        else:
            db = get_db()
            db.execute(
                "INSERT INTO students (first_name, last_name) VALUES (?, ?)",
                (first_name, last_name)
            )
            db.commit()

            return redirect("/dashboard")

    return render_template("add_student.html", error=error)


# Controller 6: Add Quiz
@app.route("/quiz/add", methods=["GET", "POST"])
def add_quiz():
    if not is_logged_in():
        return redirect("/login")

    error = None

    if request.method == "POST":
        subject = request.form.get("subject")
        num_questions = request.form.get("num_questions")
        quiz_date = request.form.get("quiz_date")

        if not subject or not num_questions or not quiz_date:
            error = "Subject, number of questions, and quiz date are required."
        else:
            db = get_db()
            db.execute(
                "INSERT INTO quizzes (subject, num_questions, quiz_date) VALUES (?, ?, ?)",
                (subject, num_questions, quiz_date)
            )
            db.commit()

            return redirect("/dashboard")

    return render_template("add_quiz.html", error=error)


# Controller 7: View Student Quiz Results
@app.route("/student/<int:student_id>")
def student_results(student_id):
    if not is_logged_in():
        return redirect("/login")

    db = get_db()

    student = db.execute(
        "SELECT * FROM students WHERE id = ?",
        (student_id,)
    ).fetchone()

    results = db.execute(
        """
        SELECT results.quiz_id, results.score, quizzes.subject, quizzes.quiz_date
        FROM results
        JOIN quizzes ON results.quiz_id = quizzes.id
        WHERE results.student_id = ?
        """,
        (student_id,)
    ).fetchall()

    return render_template("student_results.html", student=student, results=results)


# Controller 8: Add Quiz Result
@app.route("/results/add", methods=["GET", "POST"])
def add_result():
    if not is_logged_in():
        return redirect("/login")

    error = None
    db = get_db()

    students = db.execute("SELECT * FROM students").fetchall()
    quizzes = db.execute("SELECT * FROM quizzes").fetchall()

    if request.method == "POST":
        student_id = request.form.get("student_id")
        quiz_id = request.form.get("quiz_id")
        score = request.form.get("score")

        if not student_id or not quiz_id or not score:
            error = "Student, quiz, and score are required."
        else:
            score = int(score)

            if score < 0 or score > 100:
                error = "Score must be between 0 and 100."
            else:
                db.execute(
                    "INSERT INTO results (student_id, quiz_id, score) VALUES (?, ?, ?)",
                    (student_id, quiz_id, score)
                )
                db.commit()

                return redirect("/dashboard")

    return render_template("add_result.html", error=error, students=students, quizzes=quizzes)


# Run app
if __name__ == "__main__":
    if not os.path.exists(DATABASE):
        init_db()

    app.run(debug=True)
