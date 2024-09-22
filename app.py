import typing
from datetime import timedelta
import warnings

from utils import *

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
import uuid
import tomllib
import tomli_w

try:
    with open("config/config.toml", "rb") as f:
        configFileContents = tomllib.load(f)
except FileNotFoundError:
    configFileContents = {}

writeConfig = False

if not configFileContents.get("ADMIN_SECRET"):
    configFileContents["ADMIN_SECRET"] = str(uuid.uuid4())
    writeConfig = True

if not configFileContents.get("SECRET_KEY"):
    configFileContents["SECRET_KEY"] = str(uuid.uuid4())
    writeConfig = True

if writeConfig:
    with open("config/config.toml", "wb") as f:
        tomli_w.dump(configFileContents, f)


app = Flask(__name__)
app.config.from_mapping(configFileContents)
setDefaultConfigValues(app)

# We force a value here to make sure sessions persist when wishes are fulfilled
if app.config.get("PERMANENT_SESSION_LIFETIME"):
    warnings.warn(
        "Ignored setting PERMANENT_SESSION_LIFETIME, this value is not configurable.",
        RuntimeWarning,
    )
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(weeks=52 * 4)


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
db.init_app(app)

from wishes import Wishlist, SecretMismatchError, WishFulfilledError, WishNotFoundError

with app.app_context():
    db.create_all()

wishlist = Wishlist()

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
    if session.get(SESSION_NO_SPOILER):
        return redirect(url_for("noSpoilerView"))

    return render_template(
        "list.html",
        ownerName=app.config["OWNER_NAME"],
        orderedWishlist=wishlist.getPriorityOrderedWishes(
            giftedWishSecrets=session.get(SESSION_FULFILLED_WISHES, [])
        ),
        userFulfilledWishes=session.get(SESSION_FULFILLED_WISHES, []),
        loggedIn=session.get(SESSION_IS_LOGGED_IN),
    )


@app.route("/yesSpoiler")
def yesSpoiler():
    session[SESSION_NO_SPOILER] = False
    return redirect(url_for("listView"))


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
        loggedIn=session.get(SESSION_IS_LOGGED_IN),
    )


@app.route("/wishes/<int:id>", methods=["GET"])
def wishView(id):
    try:
        wish = wishlist.getWishByID(id)
    except WishNotFoundError:
        return error(
            app=app,
            code=404,
            title="Ungültige URL",
            message="Es gibt keinen Wunsch mit dieser ID.",
        )
    if wish.isFulfilled():
        return render_template(
            "wish_already_fulfilled.html",
            ownerName=app.config["OWNER_NAME"],
            loggedIn=session.get(SESSION_IS_LOGGED_IN),
        )
    return render_template(
        "wish.html",
        ownerName=app.config["OWNER_NAME"],
        wishTitle=wish.title,
        loggedIn=session.get(SESSION_IS_LOGGED_IN),
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
    except WishNotFoundError:
        return error(
            app=app,
            code=404,
            title="Ungültige URL",
            message="Es gibt keinen Wunsch mit dieser ID.",
        )
    return redirect(url_for("thankYouView", id=id, secret=secret))


@app.route("/wishes/<int:id>/<secret>", methods=["GET"])
def thankYouView(id, secret):
    try:
        wish = wishlist.getWishByID(id)
    except WishNotFoundError:
        return error(
            app=app,
            code=404,
            title="Ungültige URL",
            message="Es gibt keinen Wunsch mit dieser ID.",
        )
    if wish.secret != secret:
        return error(
            app=app,
            code=403,
            title="Ungültige URL",
            message="Das angegebene Secret passt nicht zum Wunsch.",
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
        loggedIn=session.get(SESSION_IS_LOGGED_IN),
    )


@app.route("/wishes/<int:id>/<secret>", methods=["POST"])
def undoWishFulfillFormSubmit(id, secret):
    try:
        wishlist.reopenWish(id)
    except SecretMismatchError:
        return error(
            app=app,
            code=403,
            title="Ungültige URL",
            message="Das angegebene Secret passt nicht zum Wunsch.",
        )
    except WishNotFoundError:
        return error(
            app=app,
            code=404,
            title="Ungültige URL",
            message="Es gibt keinen Wunsch mit dieser ID.",
        )
    return redirect(url_for("listView"))


@app.route("/login/<secret>", methods=["GET"])
def loginView(secret):
    if secret == app.config["ADMIN_SECRET"]:
        session[SESSION_IS_LOGGED_IN] = True
    return redirect(url_for("adminView"))


@app.route("/admin", methods=["GET"])
@admin(app)
def adminView():
    session[SESSION_NO_SPOILER] = True
    return render_template(
        "admin.html",
        loginLink=url_for("loginView", secret=app.config["ADMIN_SECRET"]),
        ownerName=app.config["OWNER_NAME"],
        orderedWishlist=wishlist.getPriorityOrderedWishesNoSpoiler(),
        stats=wishlist.getStats(),
        orderedDeletedWishlist=wishlist.getDeletedWishes(),
        loggedIn=session.get(SESSION_IS_LOGGED_IN),
    )


@app.route("/admin", methods=["POST"])
@admin(app)
def adminFormSubmit():
    if request.form["action"] == "delete":
        wishID = request.form["wishId"]
        wishlist.delWish(id=wishID)
        return render_template(
            "admin.html",
            loginLink=url_for("loginView", secret=app.config["ADMIN_SECRET"]),
            ownerName=app.config["OWNER_NAME"],
            orderedWishlist=wishlist.getPriorityOrderedWishesNoSpoiler(),
            stats=wishlist.getStats(),
            orderedDeletedWishlist=wishlist.getDeletedWishes(),
            message=f'Wunsch "{wishlist.getWishByID(wishID).title}" erfolgreich gelöscht!',
            messageUndo={"action": "restore", "wishID": wishID},
            loggedIn=session.get(SESSION_IS_LOGGED_IN),
        )
    elif request.form["action"] == "restore":
        wishID = request.form["wishId"]
        wishlist.undelWish(id=wishID)
        return render_template(
            "admin.html",
            loginLink=url_for("loginView", secret=app.config["ADMIN_SECRET"]),
            ownerName=app.config["OWNER_NAME"],
            orderedWishlist=wishlist.getPriorityOrderedWishesNoSpoiler(),
            stats=wishlist.getStats(),
            orderedDeletedWishlist=wishlist.getDeletedWishes(),
            message=f'Wunsch "{wishlist.getWishByID(wishID).title}" wurde wiederhergestellt.',
            messageUndo={"action": "delete", "wishID": wishID},
            loggedIn=session.get(SESSION_IS_LOGGED_IN),
        )
    elif request.form["action"] == "regenerateAdminLink":
        try:
            with open("config/config.toml", "rb") as f:
                configFileContents = tomllib.load(f)
        except FileNotFoundError:
            configFileContents = {}
        configFileContents["ADMIN_SECRET"] = str(uuid.uuid4())
        with open("config/config.toml", "wb") as f:
            tomli_w.dump(configFileContents, f)
        app.config.from_mapping(configFileContents)
    return redirect(url_for("adminView"))


@app.route("/admin/addWish", methods=["GET"])
@admin(app)
def addWishView():
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
        loggedIn=session.get(SESSION_IS_LOGGED_IN),
    )


@app.route("/admin/addWish", methods=["POST"])
@admin(app)
def addWishFormSubmit():
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
@admin(app)
def editWishView(id):
    try:
        wish = wishlist.getWishByID(id)
    except WishNotFoundError:
        return error(
            app=app,
            code=404,
            title="Ungültige URL",
            message="Es gibt keinen Wunsch mit dieser ID.",
        )

    session[SESSION_NO_SPOILER] = True

    return render_template(
        "upsert_wish.html",
        ownerName=app.config["OWNER_NAME"],
        template=wish,
        update=True,
        loggedIn=session.get(SESSION_IS_LOGGED_IN),
    )


@app.route("/admin/editWish/<int:id>", methods=["POST"])
@admin(app)
def editWishFormSubmit(id):
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


@app.route("/admin/logout")
@admin(app)
def logout():
    session[SESSION_IS_LOGGED_IN] = False
    return redirect(url_for("listView"))
