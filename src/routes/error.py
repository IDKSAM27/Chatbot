from flask import render_template

from ..app import app

error_codes = [403, 404, 500, 502, 503, 504, 505]

for error_code in error_codes:

    @app.errorhandler(error_code)
    def handle_error(error, error_code=error_code):
        return render_template(f"errors/{error_code}.jinja", error=error), error_code
