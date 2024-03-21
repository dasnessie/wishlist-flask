from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
  pass

app = Flask(__name__)
app.config ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wishes.sqlite3'

db = SQLAlchemy(model_class=Base)
db.init_app(app)

from wishes import Wishlist

with app.app_context():
    db.create_all()

wishlist = Wishlist()
wishlist.addWish("Shenanigans", 3, "Für mehr Blödsinn!", link = "https://youtu.be/dQw4w9WgXcQ?si=B8g9pOJgWpztlIZw")
wishlist.addWish("Weltfrieden", 5)
wishlist.addWish("Wäre ganz nett", 1, desc="Das hier wäre auch ganz nett. Ist aber nicht besonders wichtig.")

@app.route("/")
def hello_world():
    return render_template('list.html', wishlist=wishlist)