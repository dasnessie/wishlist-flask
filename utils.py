from functools import wraps
from typing import Callable
from flask import (
    Flask,
    render_template,
    session,
)

SESSION_NO_SPOILER = "noSpoiler"
SESSION_FULFILLED_WISHES = "fulfilledWishes"
SESSION_IS_LOGGED_IN = "isLoggedIn"


def setDefaultConfigValues(app):
    # Default config value dict
    defaultConfig = {
        "OWNER_NAME": "Jemand",
        "SQLALCHEMY_DATABASE_URI": "sqlite:///wishes.sqlite3",
    }
    # for any key not already set, set the default value
    for key, value in defaultConfig.items():
        if key not in app.config:
            app.config[key] = value


def admin(app: Flask):
    def adminDecorator(f: Callable):
        @wraps(f)
        def adminWrapper(*args, **kwds):
            if not session.get(SESSION_IS_LOGGED_IN, False):
                return error(
                    app,
                    code=401,
                    title="Nicht eingeloggt!",
                    message="Bitte logge dich als Admin ein, um diese Seite zu benutzen.",
                )
            return f(*args, **kwds)

        return adminWrapper

    return adminDecorator


def error(app: Flask, code: int, title: str, message: str):
    return (
        render_template(
            "error.html",
            errorTitle=title,
            errorMessage=message,
            loggedIn=session.get(SESSION_IS_LOGGED_IN),
        ),
        code,
    )
