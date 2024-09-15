def setDefaultConfigValues(app):
    # Default config value dict
    defaultConfig = {"OWNER_NAME": "Jemand"}
    # for any key not already set, set the default value
    for key, value in defaultConfig.items():
        if key not in app.config:
            app.config[key] = value
