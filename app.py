from utils import setDefaultConfigValues

from flask import Flask, render_template, request, make_response, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

import tomllib

class Base(DeclarativeBase):
  pass

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wishes.sqlite3'

try:
    app.config.from_file("config/config.toml", load=tomllib.load, text=False)
except FileNotFoundError:
    pass

setDefaultConfigValues(app)

db = SQLAlchemy(model_class=Base)
db.init_app(app)

from wishes import Wishlist

with app.app_context():
    db.create_all()

wishlist = Wishlist()
if len(wishlist.getPriorityOrderedWishes()) == 0:
    wishlist.addWish("Shenanigans", 3, desc="Für mehr Blödsinn!", link = "https://youtu.be/dQw4w9WgXcQ?si=B8g9pOJgWpztlIZw")
    wishlist.addWish("Weltfrieden", 5)
    wishlist.addWish("Wäre ganz nett", 1, desc="Das hier wäre auch ganz nett. Ist aber nicht besonders wichtig.", link="https://www.amazon.de/ganz-besonders-nette-Stra%C3%9Fenbahn-Pappbilderbuch/dp/3833908165/ref=sr_1_1?dib=eyJ2IjoiMSJ9.xxJaCG62cdpNP8ARhvl8Igybdj1J2u-XtCmpv9ckHTuudAtquX3JPTER8KtfKmuoi5cLRdoFH_xnf7Y3hcPyQlgpWT562chkYVKMUOTAlCqMebY5S4ubVNUEXHSE1VTlGG-SgbQYrbqbMW9_qe9CNvFBgO3Mqy6ortJ8QjGik6xyW0K-fq-akOTWDW8wAk_QDH9fDVdJbd2cBQSHIb71Oka1A5OBTn8leTSgGSOs8uc.reS7XCXaHsyN1ovc-MOO54YnAxW1eJi3pGDS9oD77-I&dib_tag=se&keywords=ganz+nett&qid=1711555281&sr=8-1")
    wishlist.addWish("Funktionierende Hüfte", 4, desc="Ich möchte gerne, dass meine Hüfte wieder funktioniert.", giver="Me")

@app.route("/")
def listView():
    resp = make_response(render_template('list.html', ownerName=app.config['OWNER_NAME'], orderedWishlist=wishlist.getPriorityOrderedWishes()))
    if request.args.get('yesSpoiler') == '1':
        resp.delete_cookie('noSpoiler')
    elif request.cookies.get('noSpoiler') == '1':
        return redirect(url_for('noSpoilerView'))
    return resp

@app.route("/nospoiler")
def noSpoilerRedirect():
    return redirect(url_for('noSpoilerView'))

@app.route("/noSpoiler")
def noSpoilerView():
    resp = make_response(render_template('list.html', ownerName=app.config['OWNER_NAME'], orderedWishlist=wishlist.getPriorityOrderedWishesNoSpoiler(), noSpoiler=True, stats=wishlist.getStats()))
    resp.set_cookie('noSpoiler', '1')
    return resp

@app.route("/gift<int:id>", methods=["GET"])
def giftView(id):
    return render_template('gift.html', ownerName=app.config['OWNER_NAME'], wishTitle=wishlist.getWishByID(id).title)

@app.route("/gift<int:id>", methods=["POST"])
def giftFormSubmit(id):
    giver = request.form['user_nickname']
    wishlist.markFulfilled(id, giver)
    secret = wishlist.getWishByID(id).secret
    return redirect(url_for('thankYouView', id=id, secret=secret))
    # return render_template('thankyou.html', ownerName=app.config['OWNER_NAME'], giver=giver)

@app.route("/gift<int:id>/<secret>", methods=["GET"])
def thankYouView(id, secret):
    wish = wishlist.getWishByID(id)
    if (wish.secret != secret):
        return render_template('invalid_url.html', ownerName=app.config['OWNER_NAME'], errorMessage = "Das angegebene Secret passt nicht zum Wunsch.")
    return render_template('thankyou.html', ownerName=app.config['OWNER_NAME'], wishTitle=wish.title, url=request.url)

@app.route("/gift<int:id>/<secret>", methods=["POST"])
def undoGiftFulfillFormSubmit(id, secret):
    wish = wishlist.getWishByID(id)
    if (wish.secret != secret):
        return render_template('invalid_url.html', ownerName=app.config['OWNER_NAME'], errorMessage = "Das angegebene Secret passt nicht zum Wunsch.")
    wishlist.reopenGift(id)
    return redirect(url_for('listView'))
