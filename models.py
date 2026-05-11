from datetime import datetime
from flask import url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt

db     = SQLAlchemy()
bcrypt = Bcrypt()

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    images        = db.relationship("GeneratedImage", backref="user",
                                    lazy=True, cascade="all, delete-orphan")

    def set_password(self, pw):
        self.password_hash = bcrypt.generate_password_hash(pw).decode("utf-8")

    def check_password(self, pw):
        return bcrypt.check_password_hash(self.password_hash, pw)

    def __repr__(self):
        return f"<User {self.username}>"


class GeneratedImage(db.Model):
    __tablename__   = "generated_images"
    id              = db.Column(db.Integer, primary_key=True)
    user_id         = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    filename        = db.Column(db.String(255), nullable=False)
    prompt          = db.Column(db.Text, nullable=False)
    negative_prompt = db.Column(db.Text, default="")
    model           = db.Column(db.String(120), default="")
    aspect_ratio    = db.Column(db.String(20), default="square")
    is_favorite     = db.Column(db.Boolean, default=False)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id":          self.id,
            "filename":    self.filename,
            "prompt":      self.prompt,
            "model":       self.model,
            "is_favorite": self.is_favorite,
            "created_at":  self.created_at.strftime("%b %d, %H:%M"),
            "image_url":   url_for("static", filename=f"images/{self.filename}")
        }

    def __repr__(self):
        return f"<Image {self.filename}>"