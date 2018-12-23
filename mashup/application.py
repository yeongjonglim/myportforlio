import os
import re
from flask import Flask, jsonify, render_template, request

from cs50 import SQL
from helpers import lookup

# Configure application
app = Flask(__name__)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///mashup.db")


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
def index():
    """Render map"""
    return render_template("index.html")


@app.route("/articles")
def articles():
    """Look up articles for geo"""

    # Ensure parameters are present
    if not request.args.get("geo"):
        raise RuntimeError("missing geo")
    geo = request.args.get("geo")
    src = lookup(geo)
    article = []
    for i in range(len(src)):
        if i >= 5:
            break
        article.append(src[i])

    # Output articles from lookup
    return jsonify(article)


@app.route("/search")
def search():
    """Search for places that match query"""

    # Ensure parameters are present
    if not request.args.get("q"):
        raise RuntimeError("missing q")

    # Manage the query word by word, separated by spaces or comma
    queries = re.split(', |\s+',request.args.get("q"))

    # Add wildcards for query
    wildcard = "* "
    query = wildcard.join(queries)
    query = query + wildcard

    # Query the virtual table with a specific column arrangement
    rows=db.execute("""SELECT accuracy, admin_code1, admin_code2, admin_code3, admin_name1, admin_name2, admin_name3, country_code, latitude, longitude, place_name, postal_code
                    FROM places WHERE places MATCH :q;""", q=query)

    # Return query as tuple
    return jsonify(rows)


@app.route("/update")
def update():
    """Find up to 10 places within view"""

    # Ensure parameters are present
    if not request.args.get("sw"):
        raise RuntimeError("missing sw")
    if not request.args.get("ne"):
        raise RuntimeError("missing ne")

    # Ensure parameters are in lat,lng format
    if not re.search("^-?\d+(?:\.\d+)?,-?\d+(?:\.\d+)?$", request.args.get("sw")):
        raise RuntimeError("invalid sw")
    if not re.search("^-?\d+(?:\.\d+)?,-?\d+(?:\.\d+)?$", request.args.get("ne")):
        raise RuntimeError("invalid ne")

    # Explode southwest corner into two variables
    sw_lat, sw_lng = map(float, request.args.get("sw").split(","))

    # Explode northeast corner into two variables
    ne_lat, ne_lng = map(float, request.args.get("ne").split(","))

    # Virtual tables don't read negative sign, but only read the nominal values
    rows = db.execute("""SELECT * FROM places
                        WHERE ':sw_lat' <= latitude AND latitude <= ':ne_lat' AND (':sw_lng' >= longitude AND longitude >= ':ne_lng')
                        GROUP BY country_code, place_name, admin_code1
                        ORDER BY RANDOM()
                        LIMIT 10""",
                        sw_lat=sw_lat, ne_lat=ne_lat, sw_lng=sw_lng, ne_lng=ne_lng)

    # Find 10 cities within view, pseudorandomly chosen if more within view
    # if sw_lng <= ne_lng:

    #     # Doesn't cross the antimeridian
    #     rows = db.execute("""SELECT * FROM places
    #                       WHERE ':sw_lat' <= latitude AND latitude <= ':ne_lat' AND (':sw_lng' <= longitude AND longitude <= ':ne_lng')
    #                       GROUP BY country_code, place_name, admin_code1
    #                       ORDER BY RANDOM()
    #                       LIMIT 10""",
    #                       sw_lat=sw_lat, ne_lat=ne_lat, sw_lng=sw_lng, ne_lng=ne_lng)

    # else:

    #     # Crosses the antimeridian
    #     rows = db.execute("""SELECT * FROM places
    #                       WHERE ':sw_lat' <= latitude AND latitude <= ':ne_lat' AND (':sw_lng' <= longitude OR longitude <= ':ne_lng')
    #                       GROUP BY country_code, place_name, admin_code1
    #                       ORDER BY RANDOM()
    #                       LIMIT 10""",
    #                       sw_lat=sw_lat, ne_lat=ne_lat, sw_lng=sw_lng, ne_lng=ne_lng)

    # Output places as JSON
    return jsonify(rows)
