from flask import Flask, render_template, request, redirect, url_for, make_response
import hashlib, uuid
from models.user import User
from models.settings import db

app = Flask(__name__)
db.create_all()

@app.route('/')
def index():
    # check if user is authenticated based on session_token
    session_token = request.cookies.get("session_token")

    user = db.query(User).filter_by(session_token=session_token).first()

    return render_template("index.html", user=user)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")

    elif request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        repeat = request.form.get("repeat")

        if password != repeat:
            return "Passwords don't match! Go back and try again."

        user = User(username=username, password_hash=hashlib.sha256(password.encode()).hexdigest(),session_token=str(uuid.uuid4()))
        db.add(user)  # add to the transaction (user is not yet in a database)
        db.commit()  # commit the transaction into the database (user is now added in the database)
        response = make_response(redirect(url_for('index')))
        response.set_cookie("session_token", user.session_token, httponly=True, samesite='Strict')

        return response


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    elif request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # get password hash out of password
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        # get user from database by her/his username and password
        user = db.query(User).filter_by(username=username).first()

        if not user:
            return "This user does not exist"
        else:
            # if user exists, check if password hashes match
            if password_hash == user.password_hash:
                user.session_token = str(uuid.uuid4())  # if password hashes match, create a session token
                db.add(user)
                db.commit()

                # save user's session token into a cookie
                response = make_response(redirect(url_for('index')))
                response.set_cookie("session_token", user.session_token, httponly=True, samesite='Strict')

                return response
            else:
                return "Your password is incorrect!"

# this is just a regular way how to run some Python file safely
if __name__ == '__main__':
    app.run()