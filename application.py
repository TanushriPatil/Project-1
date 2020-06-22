import os
import csv
import requests

from flask import Flask, render_template, request, redirect, url_for, jsonify, g
from flask import session
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


app = Flask(__name__)
app.secret_key = 'x\xd8$y\xa7\x87<`\xb9\x81"\xd4\xfb.\xb0\xe5B\xae4?\x98\xa6\xc2/'

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login")
def index2():
    return render_template("index2.html")

@app.route("/register", methods=["POST"])
def register():

    name = request.form.get("name")
    username = request.form.get("username")
    password = request.form.get("password")
#        age = int(request.form.get("age"))
    try:
        age = int(request.form.get("age"))
#        if age <= 0 :
#            return render_template("error.html", msg="enter valid age")
    except ValueError:
        return render_template("error.html", msg="Type valid age")

    if db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).rowcount == 1:
        return render_template("error.html", msg="username exists")
    if not password:
        return render_template("error.html", msg="Password field empty")

    if not name:
        return render_template("error.html", msg = "Name field is empty")

    db.execute("INSERT INTO users (name, username, password, age) VALUES (:name, :username, :password, :age)", {"name": name, "username": username, "password": password, "age": age})
    db.commit()
    return render_template("successr.html", message = "Successful registration")

@app.before_request
def before_request():
    g.username = None

    if 'username' in session:
        g.username = session['username']

@app.route("/login/loggedin", methods = ["POST"])
def login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")

        if db.execute("SELECT * FROM users WHERE username = :username AND password = :password", {"username": username, "password": password}).rowcount == 1:
            session['username'] = username
        else:
            return render_template("error.html", msg = "Please enter valid login credentials or register")


    return redirect(url_for('search'))

@app.route("/logout")
def logout():
    if g.username:
        session.pop('username', None)
        return redirect(url_for("index2"))

@app.route("/login/loggedin/notes/", methods = ["GET", "POST"])
def notes():

    if 'notes' in session:
        if session.get("notes") is None:
            session["notes"] = []
        if request.method == "POST":
            note = request.form.get("note")
            session["notes"].append(note)

    return render_template("notes.html", msg = "hey user", notes = session["notes"])


@app.route("/loggedin/search", methods = ["GET", "POST"])
def search():
    if g.username:
        if request.method == "POST":
            book = request.form.get("book")
            book = book.lower()

            data = db.execute("SELECT * FROM books WHERE isbn LIKE :book OR Lower(title) LIKE :book OR Lower(author) LIKE :book ", {"book": f"%{book}%"}).fetchall()

            if not 'data':
                return render_template("error.html", msg = "Couldn't find the required book. Try again!")
            else:
                return render_template("search.html", data = data)
                db.commit()
        return render_template("search.html")
    return redirect(url_for("index2"))

@app.route("/loggedin/search/book", methods = ["GET", "POST"])
def display():

    if g.username:

        selected_book = request.args.get('type')
        res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "4orjTp2KQbq4lsHgvCSr6A", "isbns": selected_book})
        if res.status_code != 200:
            raise Exception("Error: Page not found. Try again!!")
        data = res.json()

        book_id = data["books"][0]["id"]
        book_isbn = data["books"][0]["isbn"]
        book_rating = data["books"][0]["average_rating"]

        reviews = db.execute("SELECT * FROM reviews WHERE isbn = :isbn", {"isbn": selected_book}).fetchall()

        avg_rating = db.execute("SELECT avg_score FROM books WHERE isbn = :isbn", {"isbn": selected_book}).fetchone()
    #    book_title = db.execute("SELECT title FROM books WHERE isbn = :isbn", {"isbn": selected_book}).fetchone()
    #    book_author = db.execute("SELECT author FROM books WHERE isbn = :isbn", {"isbn": selected_book}).fetchone()
        data = db.execute("SELECT title, author FROM books WHERE isbn = :isbn", {"isbn": selected_book}).fetchall()
        db.commit()

        return render_template("response.html", data=data, book_id = book_id, book_isbn = book_isbn, book_rating = book_rating, avg_rating = avg_rating, reviews = reviews, username=g.username)
    return redirect(url_for("index2"))

@app.route("/search/book/review", methods = ["GET", "POST"] )
def review():

    if g.username:
        selected_book = request.args.get('type')
        scale = request.form["rate"]
        if request.method == "POST":
            if db.execute("SELECT * FROM reviews WHERE username = :username AND isbn = :isbn", {"username": g.username, "isbn": selected_book}).rowcount == 0:
                latest_review = request.form.get("review")

                db.execute("INSERT INTO reviews (username, review, isbn, scale) VALUES (:username, :review, :isbn, :scale)", {"username": g.username, "review": latest_review, "isbn": selected_book, "scale": scale})

                db. execute("UPDATE books SET (review_count, avg_score) = (SELECT COUNT(*), AVG(scale) FROM reviews WHERE isbn=:isbn) WHERE isbn=:isbn", {"isbn": selected_book, "isbn": selected_book})

                db.commit()
                return redirect(url_for("display", type = selected_book))
            else:
                return f"<h2>Review already given</h2>"
    return redirect(url_for("index2"))

@app.route("/loggedin/write_review")
def write_review():
    return render_template("review.html")


@app.route("/api/<isbn>")
def book_api(isbn):
    if db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).rowcount == 0:
        return jsonify({"error": "Invalid isbn"}), 404
    books = db.execute("SELECT * FROM books where isbn = :isbn",{"isbn": isbn}).fetchall()
    return jsonify({'books': [dict(row) for row in books]})
