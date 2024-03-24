from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
  pass

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wishes.sqlite3'

db = SQLAlchemy(model_class=Base)
db.init_app(app)

from wishes import Wishlist

with app.app_context():
    db.create_all()

wishlist = Wishlist()
if len(wishlist.getPriorityOrderedWishes()) == 0:
    wishlist.addWish("Shenanigans", 3, desc="Für mehr Blödsinn!", link = "https://youtu.be/dQw4w9WgXcQ?si=B8g9pOJgWpztlIZw")
    wishlist.addWish("Weltfrieden", 5)
    wishlist.addWish("Wäre ganz nett", 1, desc="Das hier wäre auch ganz nett. Ist aber nicht besonders wichtig.")
    wishlist.addWish("Funktionierende Hüfte", 4, desc="Ich möchte gerne, dass meine Hüfte wieder funktioniert", giver="Me")

@app.route("/")
def listView():
    return render_template('list.html', orderedWishlist=wishlist.getPriorityOrderedWishes())

@app.route("/nospoiler")
def noSpoilerView():
    return render_template('list.html', orderedWishlist=wishlist.getPriorityOrderedWishesNoSpoiler(), noSpoiler=True, stats=wishlist.getStats())