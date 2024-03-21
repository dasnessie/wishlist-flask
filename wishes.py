from sqlalchemy import Integer, String, select
from sqlalchemy.orm import Mapped, mapped_column

from app import db, app

class Wishlist:
    def __init__(self):
        self.db = db
    
    def addWish(self, title:str, priority:int, desc:str = '', link:str = '', endless:bool = False ,giver:str = '', secret:str = ''):
        with app.app_context():
            db.session.add(Wish(title, priority, desc, link, endless, giver, secret))
            db.session.commit()

    def getPriorityOrderedWishes(self):
        wishes = []
        with app.app_context():
            wishes = db.session.scalars(select(Wish).order_by(Wish.priority.desc())).all()
        return wishes

class Wish(db.Model):
    __tablename__ = "wishes"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    priority: Mapped[int]
    desc: Mapped[str]
    link: Mapped[str]
    endless: Mapped[bool]
    giver: Mapped[str]
    secret: Mapped[str] # = mapped_column(unique=True)

    def __init__(self, title:str, priority:int, desc:str = '', link:str = '', endless:bool = False ,giver:str = '', secret:str = ''):
        """
        Args:
            title (str): title of the wish
            priority (int): how important the wish is (min 1, max 5)
            desc (str, optional): description text. Defaults to ''.
            link (str, optional): link to shop etc. Defaults to ''.
            endless (bool, optional): If this is True, wish can not be marked as done. Defaults to False.
            giver (str, optional): Name of person gifting the thing. If empty, then wish still open. Defaults to ''.
            secret (str, optional): secret of link to mark wish as open again. Defaults to ''.
        """
        self.title = title
        if priority < 1 or priority > 5:
            raise ValueError("priority must be between 1 and 5.")
        self.priority = priority
        self.desc = desc
        self.link = link
        self.endless = endless
        self.giver = giver
        self.secret = secret


