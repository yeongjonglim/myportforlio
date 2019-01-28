from flask import flash, redirect, render_template, request, session, url_for

from .blueprint import home

# Ensure responses aren't cached
@home.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@home.route("/")
def index():
    return render_template("home.html")
