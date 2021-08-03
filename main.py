from flask import Flask, render_template, request, redirect, url_for, make_response
import hashlib, uuid
from models.user import User
from models.topic import Topic
from models.settings import db
import smartninja_redis
import os

redis = smartninja_redis.from_url(os.environ.get("REDIS_URL"))

app = Flask(__name__)
db.create_all()


@app.route('/')
def index():
    # check if user is authenticated based on session_token
    session_token = request.cookies.get("session_token")
    user = db.query(User).filter_by(session_token=session_token).first()
    # get all topics from db
    topics = db.query(Topic).all()

    return render_template("index.html", user=user, topics=topics)


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

        user = User(username=username, password_hash=hashlib.sha256(password.encode()).hexdigest(), session_token=str(uuid.uuid4()))
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


@app.route("/create-topic", methods=["GET", "POST"])
def topic_create():
    # get current user (author)
    session_token = request.cookies.get("session_token")
    user = db.query(User).filter_by(session_token=session_token).first()
    # only logged in users can create a topic
    if not user:
        return redirect(url_for('login'))

    if request.method == "GET":
        csrf_token = str(uuid.uuid4())  # create CSRF token

        redis.set(name=csrf_token, value=user.username)  # store CSRF token into Redis for that specific user

        return render_template("topic_create.html", user=user,
                               csrf_token=csrf_token)  # send CSRF token into HTML template
    elif request.method == "POST":
        csrf = request.form.get("csrf")  # csrf from HTML
        #moj kod umjesto
        #redis_csrf_username = redis.get(name=csrf).decode()   #username value stored under the csrf name from redis
        redisime=redis.get(name=csrf)
        #print(redisime)
        if redisime:
            redis_csrf_username=redisime.decode()
            #print(redis_csrf_username)
            if  redis_csrf_username == user.username:  # if they match, allow user to create a topic
                title = request.form.get("title")
                text = request.form.get("text")

                # create a Topic object
                topic = Topic.create(title=title, text=text, author=user)

                return redirect(url_for('index'))
        else:
            #print(csrf)
            return render_template("err-csrf.html", poruka="CSRF token is not valid!")


@app.route("/topic/<topic_id>", methods=["GET"])
def topic_details(topic_id):
    topic = db.query(Topic).get(int(topic_id))

    # get current user (author)
    session_token = request.cookies.get("session_token")
    user = db.query(User).filter_by(session_token=session_token).first()

    return render_template("topic_details.html", topic=topic, user=user)


@app.route("/topic/<topic_id>/edit", methods=["GET", "POST"])
def topic_edit(topic_id):
    topic = db.query(Topic).get(int(topic_id))

    if request.method == "GET":
        return render_template("topic_edit.html", topic=topic)

    elif request.method == "POST":
        title = request.form.get("title")
        text = request.form.get("text")

        # get current user (author)
        session_token = request.cookies.get("session_token")
        user = db.query(User).filter_by(session_token=session_token).first()

        # check if user is logged in and user is author
        if not user:
            return redirect(url_for('login'))
        elif topic.author.id != user.id:
            return "You are not the author!"
        else:
            # update the topic fields
            topic.title = title
            topic.text = text
            db.add(topic)
            db.commit()

            return redirect(url_for('topic_details', topic_id=topic_id))


@app.route("/topic/<topic_id>/delete", methods=["GET", "POST"])
def topic_delete(topic_id):
    topic = db.query(Topic).get(int(topic_id))

    if request.method == "GET":
        return render_template("topic_delete.html", topic=topic)

    elif request.method == "POST":
        # print(request.form)
        if 'del' in request.form:
            db.delete(topic)
            db.commit()

    return redirect(url_for('index'))


# this is just a regular way how to run some Python file safely
if __name__ == '__main__':
    app.run()