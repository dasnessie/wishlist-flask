import typing
from datetime import timedelta

from utils import setDefaultConfigValues

from flask import (
    Flask,
    render_template,
    request,
    make_response,
    redirect,
    url_for,
    session,
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

import tomllib


class Base(DeclarativeBase):
    pass


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///wishes.sqlite3"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(weeks=52 * 4)


try:
    app.config.from_file("config/config.toml", load=tomllib.load, text=False)
except FileNotFoundError:
    pass

setDefaultConfigValues(app)

db = SQLAlchemy(model_class=Base)
db.init_app(app)

from wishes import Wishlist, SecretMismatchError, WishFulfilledError, WishNotFoundError

with app.app_context():
    db.create_all()

wishlist = Wishlist()

SESSION_NO_SPOILER = "noSpoiler"
SESSION_FULFILLED_WISHES = "fulfilledWishes"

# DEBUG
# TODO: Remove
if len(wishlist.getPriorityOrderedWishes()) == 0:
    wishlist.addWish(
        "Shenanigans",
        3,
        desc="Für mehr Blödsinn!",
        link="https://youtu.be/dQw4w9WgXcQ?si=B8g9pOJgWpztlIZw",
    )
    wishlist.addWish("Weltfrieden", 5)
    wishlist.addWish(
        "Wäre ganz nett",
        1,
        desc="Das hier wäre auch ganz nett. Ist aber nicht besonders wichtig.",
        link="https://www.amazon.de/ganz-besonders-nette-Stra%C3%9Fenbahn-Pappbilderbuch/dp/3833908165/ref=sr_1_1?dib=eyJ2IjoiMSJ9.xxJaCG62cdpNP8ARhvl8Igybdj1J2u-XtCmpv9ckHTuudAtquX3JPTER8KtfKmuoi5cLRdoFH_xnf7Y3hcPyQlgpWT562chkYVKMUOTAlCqMebY5S4ubVNUEXHSE1VTlGG-SgbQYrbqbMW9_qe9CNvFBgO3Mqy6ortJ8QjGik6xyW0K-fq-akOTWDW8wAk_QDH9fDVdJbd2cBQSHIb71Oka1A5OBTn8leTSgGSOs8uc.reS7XCXaHsyN1ovc-MOO54YnAxW1eJi3pGDS9oD77-I&dib_tag=se&keywords=ganz+nett&qid=1711555281&sr=8-1",
    )
    wishlist.addWish(
        "Funktionierende Hüfte",
        4,
        desc="Ich möchte gerne, dass meine Hüfte wieder funktioniert.",
        giver="Me",
    )


@app.before_request
def make_session_permanent():
    session.permanent = True


@app.route("/")
def listView():
    if request.args.get("yesSpoiler") == "1":
        session[SESSION_NO_SPOILER] = False
    elif session[SESSION_NO_SPOILER]:
        return redirect(url_for("noSpoilerView"))

    return render_template(
        "list.html",
        ownerName=app.config["OWNER_NAME"],
        orderedWishlist=wishlist.getPriorityOrderedWishes(
            giftedWishSecrets=session.get(SESSION_FULFILLED_WISHES, [])
        ),
        userFulfilledWishes=session.get(SESSION_FULFILLED_WISHES, []),
    )


# TODO remove once we have a general solution for wrongly cased routes (See #8)
@app.route("/nospoiler")
def noSpoilerRedirect():
    return redirect(url_for("noSpoilerView"))


@app.route("/noSpoiler")
def noSpoilerView():
    session[SESSION_NO_SPOILER] = True
    return render_template(
        "list.html",
        ownerName=app.config["OWNER_NAME"],
        orderedWishlist=wishlist.getPriorityOrderedWishesNoSpoiler(
            giftedWishSecrets=session.get(SESSION_FULFILLED_WISHES, [])
        ),
        noSpoiler=True,
        stats=wishlist.getStats(),
        userFulfilledWishes=session.get(SESSION_FULFILLED_WISHES, []),
    )


@app.route("/wishes/<int:id>", methods=["GET"])
def wishView(id):
    try:
        wish = wishlist.getWishByID(id)
    except WishNotFoundError as e:
        return (
            render_template(
                "invalid_url.html",
                ownerName=app.config["OWNER_NAME"],
                errorMessage=str(e),
            ),
            404,
        )
    if wish.isFulfilled():
        return render_template(
            "wish_already_fulfilled.html", ownerName=app.config["OWNER_NAME"]
        )
    return render_template(
        "wish.html", ownerName=app.config["OWNER_NAME"], wishTitle=wish.title
    )


@app.route("/wishes/<int:id>", methods=["POST"])
def wishFormSubmit(id):
    giver = request.form["user_nickname"]
    try:
        try:
            wishlist.markFulfilled(id, giver)
        except WishFulfilledError:
            return render_template(
                "wish_already_fulfilled.html", ownerName=app.config["OWNER_NAME"]
            )
        secret = wishlist.getWishByID(id).secret
    except WishNotFoundError as e:
        return (
            render_template(
                "invalid_url.html",
                ownerName=app.config["OWNER_NAME"],
                errorMessage=str(e),
            ),
            404,
        )
    return redirect(url_for("thankYouView", id=id, secret=secret))
    # return render_template('thank_you.html', ownerName=app.config['OWNER_NAME'], giver=giver)


@app.route("/wishes/<int:id>/<secret>", methods=["GET"])
def thankYouView(id, secret):
    try:
        wish = wishlist.getWishByID(id)
    except WishNotFoundError as e:
        return (
            render_template(
                "invalid_url.html",
                ownerName=app.config["OWNER_NAME"],
                errorMessage=str(e),
            ),
            404,
        )
    if wish.secret != secret:
        return (
            render_template(
                "invalid_url.html",
                ownerName=app.config["OWNER_NAME"],
                errorMessage="Das angegebene Secret passt nicht zum Wunsch.",
            ),
            403,
        )

    if not session.get(SESSION_FULFILLED_WISHES):
        session[SESSION_FULFILLED_WISHES] = []
    fulfilledWishesSet = set(session[SESSION_FULFILLED_WISHES])
    fulfilledWishesSet.add(secret)
    session[SESSION_FULFILLED_WISHES] = list(fulfilledWishesSet)

    return render_template(
        "thank_you.html",
        ownerName=app.config["OWNER_NAME"],
        wishTitle=wish.title,
        url=request.url,
    )


@app.route("/wishes/<int:id>/<secret>", methods=["POST"])
def undoWishFulfillFormSubmit(id, secret):
    try:
        wishlist.reopenWish(id)
    except SecretMismatchError:
        return (
            render_template(
                "invalid_url.html",
                ownerName=app.config["OWNER_NAME"],
                errorMessage="Das angegebene Secret passt nicht zum Wunsch.",
            ),
            403,
        )
    except WishNotFoundError as e:
        return (
            render_template(
                "invalid_url.html",
                ownerName=app.config["OWNER_NAME"],
                errorMessage=str(e),
            ),
            404,
        )
    return redirect(url_for("listView"))


@app.route("/admin", methods=["GET"])
def adminView():
    # TODO: Check if user is logged in as admin!
    session[SESSION_NO_SPOILER] = True
    return render_template(
        "admin.html",
        ownerName=app.config["OWNER_NAME"],
        orderedWishlist=wishlist.getPriorityOrderedWishesNoSpoiler(),
        stats=wishlist.getStats(),
        orderedDeletedWishlist=wishlist.getDeletedWishes(),
    )


@app.route("/admin", methods=["POST"])
def adminFormSubmit():
    # TODO: Check if user is logged in as admin!

    if request.form["action"] == "delete":
        wishID = request.form["wishId"]
        wishlist.delWish(id=wishID)
        return render_template(
            "admin.html",
            ownerName=app.config["OWNER_NAME"],
            orderedWishlist=wishlist.getPriorityOrderedWishesNoSpoiler(),
            stats=wishlist.getStats(),
            orderedDeletedWishlist=wishlist.getDeletedWishes(),
            message=f'Wunsch "{wishlist.getWishByID(wishID).title}" erfolgreich gelöscht!',
            messageUndo={"action": "restore", "wishID": wishID},
        )
    elif request.form["action"] == "restore":
        wishID = request.form["wishId"]
        wishlist.undelWish(id=wishID)
        return render_template(
            "admin.html",
            ownerName=app.config["OWNER_NAME"],
            orderedWishlist=wishlist.getPriorityOrderedWishesNoSpoiler(),
            stats=wishlist.getStats(),
            orderedDeletedWishlist=wishlist.getDeletedWishes(),
            message=f'Wunsch "{wishlist.getWishByID(wishID).title}" wurde wiederhergestellt.',
            messageUndo={"action": "delete", "wishID": wishID},
        )
    return redirect(url_for("adminView"))


@app.route("/admin/addWish", methods=["GET"])
def addWishView():
    # TODO: Check if user is logged in as admin!

    template = None
    if request.args.get("copy"):
        try:
            template = wishlist.getWishByID(request.args.get("copy"))
        except WishNotFoundError:
            pass

    session[SESSION_NO_SPOILER] = True

    return render_template(
        "upsert_wish.html",
        ownerName=app.config["OWNER_NAME"],
        template=template,
    )


@app.route("/admin/addWish", methods=["POST"])
def addWishFormSubmit():
    # TODO: Check if user is logged in as admin!
    wishlist.addWish(
        title=request.form["title"],
        priority=int(request.form["priority"]),
        desc=request.form["desc"],
        link=request.form["link"],
        endless=("endless" in request.form),
        giver=request.form["giver"],
    )
    return redirect(url_for("adminView"))


@app.route("/admin/editWish/<int:id>", methods=["GET"])
def editWishView(id):
    # TODO: Check if user is logged in as admin!

    try:
        wish = wishlist.getWishByID(id)
    except WishNotFoundError as e:
        return (
            render_template(
                "invalid_url.html",
                ownerName=app.config["OWNER_NAME"],
                errorMessage=str(e),
            ),
            404,
        )

    session[SESSION_NO_SPOILER] = True

    return render_template(
        "upsert_wish.html",
        ownerName=app.config["OWNER_NAME"],
        template=wish,
        update=True,
    )


@app.route("/admin/editWish/<int:id>", methods=["POST"])
def editWishFormSubmit(id):
    # TODO: Check if user is logged in as admin!
    wishlist.modifyWish(
        id=id,
        title=request.form["title"],
        priority=int(request.form["priority"]),
        desc=request.form["desc"],
        link=request.form["link"],
        endless=("endless" in request.form),
        giver=request.form["giver"],
    )
    return redirect(url_for("adminView"))
