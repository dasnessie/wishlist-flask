from sqlalchemy import Integer, String, select
from sqlalchemy.orm import Mapped, mapped_column
from urllib.parse import urlparse
from uuid import uuid4
from datetime import datetime

from app import db, app


class Wishlist:
    def __init__(self):
        self.db = db

    def addWish(
        self,
        title: str,
        priority: int,
        desc: str = "",
        link: str = "",
        endless: bool = False,
        giver: str = "",
        secret: str = "",
        deleted: datetime = None,
    ):
        with app.app_context():
            db.session.add(
                Wish(
                    title,
                    priority,
                    desc=desc,
                    link=link,
                    endless=endless,
                    giver=giver,
                    secret=secret,
                    deleted=deleted,
                )
            )
            db.session.commit()

    def delWish(self, id="", secret=""):
        with app.app_context():
            if secret:
                id = self.getIDBySecret(secret)
            elif not id:
                raise AttributeError("Need to give wish id or secret!")
            else:
                wish = self.__dbCallGetWishById(id)

            wish.delete()
            db.session.commit()

    def undelWish(self, id="", secret=""):
        with app.app_context():
            if secret:
                id = self.getIDBySecret(secret)
            elif not id:
                raise AttributeError("Need to give wish id or secret!")
            else:
                wish = self.__dbCallGetWishById(id)

            wish.undelete()
            db.session.commit()

    def getPriorityOrderedWishes(self, giftedWishSecrets=[]):
        with app.app_context():
            wishes = db.session.scalars(
                select(Wish)
                .where(Wish.deleted == None)
                .order_by(
                    (Wish.giver == "").desc(),
                    (Wish.secret.in_(giftedWishSecrets)).desc(),
                    Wish.priority.desc(),
                )
            ).all()
        return wishes

    def getPriorityOrderedWishesNoSpoiler(self, giftedWishSecrets=[]):
        with app.app_context():
            wishes = db.session.scalars(
                select(Wish)
                .where(Wish.deleted == None)
                .order_by(
                    (Wish.secret.in_(giftedWishSecrets)),
                    Wish.priority.desc(),
                )
            ).all()
        return wishes

    def getDeletedWishes(self):
        with app.app_context():
            wishes = db.session.scalars(
                select(Wish).where(Wish.deleted != None).order_by(Wish.deleted.desc())
            ).all()
        return wishes

    def getStats(self):
        with app.app_context():
            stats = {}
            stats["count"] = db.session.query(Wish).filter(Wish.deleted == None).count()
            stats["fulfilled"] = (
                db.session.query(Wish)
                .filter((Wish.deleted == None) & (Wish.giver != ""))
                .count()
            )
            stats["nrDeleted"] = (
                db.session.query(Wish).filter(Wish.deleted != None).count()
            )
        return stats

    def getWishByID(self, id):
        with app.app_context():
            wish = self.__dbCallGetWishById(id)
        return wish

    def getWishBySecret(self, secret):
        with app.app_context():
            wish = db.session.scalars(select(Wish).where(Wish.secret == secret)).first()
            if wish == None:
                raise WishNotFoundError(wishId=secret)
        return wish

    def getIDBySecret(self, secret):
        id = self.getWishBySecret(secret).id
        return id

    def markFulfilled(self, id, giver):
        with app.app_context():
            wish = self.__dbCallGetWishById(id)
            wish.markFulfilled(giver)
            db.session.commit()

    def reopenWish(self, id):
        with app.app_context():
            wish = self.__dbCallGetWishById(id)
            wish.reopen()
            db.session.commit()

    def __dbCallGetWishById(self, wishId):
        """
        Get a wish from the db by it's ID.
        Only works if called within the app.app_context().

        Args:
            wishId (int): ID of the wish

        Raises:
            WishNotFoundError: Is raised if there is no wish with that ID in the DB.

        Returns:
            wish with the given ID
        """
        wish = db.session.scalars(select(Wish).where(Wish.id == wishId)).first()
        if wish == None:
            raise WishNotFoundError(wishId=wishId)
        return wish


class Wish(db.Model):
    __tablename__ = "wishes"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    priority: Mapped[int]
    desc: Mapped[str]
    link: Mapped[str]
    endless: Mapped[bool]
    giver: Mapped[str]
    secret: Mapped[str]  # = mapped_column(unique=True)
    deleted: Mapped[datetime] = mapped_column(nullable=True)

    def __init__(
        self,
        title: str,
        priority: int,
        desc: str = "",
        link: str = "",
        endless: bool = False,
        giver: str = "",
        secret: str = "",
        deleted: datetime = None,
    ):
        """
        Args:
            title (str): title of the wish
            priority (int): how important the wish is (min 1, max 5)
            desc (str, optional): description text. Defaults to ''.
            link (str, optional): link to shop etc. Defaults to ''.
            endless (bool, optional): If this is True, wish can not be marked as done. Defaults to False.
            giver (str, optional): Name of person gifting the thing. If empty, then wish still open. Defaults to ''.
            secret (str, optional): secret of link to mark wish as open again. Defaults to ''.
            deleted (datetime, optional): If not none: time at which the wish was deleted (None if wish is not deleted)
        """
        if len(title.strip()) == 0:
            raise ValueError("Title must not be empty.")
        self.title = title.strip()
        if priority < 1 or priority > 5:
            raise ValueError("Priority must be between 1 and 5.")
        self.priority = priority
        self.desc = desc
        self.link = link
        self.endless = endless
        self.giver = giver
        self.secret = secret
        self.deleted = deleted

    def getLinkDomain(self):
        parsedLink = urlparse(self.link)
        domain = parsedLink.netloc

        # Remove any leading "www." from the domain
        if domain.startswith("www."):
            domain = domain[4:]

        return domain

    def isFulfilled(self):
        return self.giver != ""

    def markFulfilled(self, giver: str):
        if self.isFulfilled():
            raise WishFulfilledError()
        self.giver = giver
        self.secret = uuid4().hex

    def reopen(self):
        self.giver = ""
        self.secret = ""

    def hasMatchingSecretIn(self, secrets):
        return self.secret in secrets

    def delete(self):
        if self.deleted == None:
            self.deleted = datetime.now()

    def undelete(self):
        self.deleted = None


class WishNotFoundError(ValueError):
    def __init__(self, wishId, *args):
        super().__init__(args)
        self.wishId = wishId

    def __str__(self):
        return f"There is no wish with ID {self.wishId}."


class SecretMismatchError(ValueError):
    def __init__(self, *args):
        super().__init__(args)

    def __str__(self):
        return f"The given secret does not match the wishes secret!"


class WishFulfilledError(ValueError):
    def __init__(self, *args):
        super().__init__(args)

    def __str__(self):
        return f"The wish is already fulfilled!"
