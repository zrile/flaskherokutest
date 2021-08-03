from models.settings import db
from datetime import datetime

class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    text = db.Column(db.String)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # foreign key (table name for the User model is "users")
    author = db.relationship("User")  # not a real field, just shows a relationship with the User model
    created = db.Column(db.DateTime, default=datetime.utcnow)

@classmethod
def create(cls, title, text, author):
    topic = cls(title=title, text=text, author=author)
    db.add(topic)
    db.commit()

    return topic