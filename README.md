# Wishlist-flask

A simple wish list website written in flask.

Features include:

- Site visitors can mark wishes as done, and if they need to, mark them as open again later
- Spoiler-free view and stats for the list owner
- Many customization options

## Config

The following values can be set in `config/config.toml`:

- `OWNER_NAME`: The name that should be displayed in the header. Defaults to "Jemand".
- `SERVER_NAME`: Your server's host, e.g. `wishlist.example.com:3000`. Used to build the url to reopen wishes for your site visitors.
- `PREFERRED_URL_SCHEME`: Your server's URL scheme, e.g. `https`. Used to build the url to reopen wishes for your site visitors.
- `SECRET_KEY`: Secret key to encrypt the session data with. Please use your favorite password generator.
- `ADMIN_SECRET`: Secret to login in as admin. The admin url will be `$PREFERRED_URL_SCHEME://$SERVER_NAME/$ADMIN_SECRET`. Please use your favorite password generator.
