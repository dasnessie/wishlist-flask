from flask import Flask, render_template, request, make_response, redirect, url_for
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
    resp = make_response(render_template('list.html', orderedWishlist=wishlist.getPriorityOrderedWishes()))
    if request.args.get('yesSpoiler') == '1':
        resp.delete_cookie('noSpoiler')
    elif request.cookies.get('noSpoiler') == '1':
        return redirect(url_for('noSpoilerView'))
    return resp

@app.route("/nospoiler")
def noSpoilerView():
    resp = make_response(render_template('list.html', orderedWishlist=wishlist.getPriorityOrderedWishesNoSpoiler(), noSpoiler=True, stats=wishlist.getStats()))
    resp.set_cookie('noSpoiler', '1')
    return resp