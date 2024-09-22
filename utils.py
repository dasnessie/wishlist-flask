from flask import Flask, render_template


def setDefaultConfigValues(app):
    # Default config value dict
    defaultConfig = {"OWNER_NAME": "Jemand"}
    # for any key not already set, set the default value
    for key, value in defaultConfig.items():
        if key not in app.config:
            app.config[key] = value


def error(app: Flask, code: int, title: str, message: str):
    return (
        render_template(
            "error.html",
            ownerName=app.config["OWNER_NAME"],
            errorTitle=title,
            errorMessage=message,
        ),
        code,
    )
