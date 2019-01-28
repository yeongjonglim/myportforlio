from flask import flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from .helpers import apology, login_required, lookup, usd, checkpwstr
from .blueprint import finance
from .models import *

# Custom filter
#app.jinja_env.filters["usd"] = usd

# Ensure responses aren't cached
@finance.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@finance.route("/index")
@login_required
def index():
    """Show portfolio of stocks"""
    # Query database for what the user currently has
    stocksown = stockview(session.get('user_id'))
    userin = Users.query.filter_by(uid=session.get('user_id')).first()

    # Lookup for stocks' current price
    indlookup = []
    for stock in stocksown:
       indlookup.append(lookup(stock['symbol']))
    return render_template("finance.html", stocksinfo=indlookup, stocksowned=stocksown, usercash=float(userin.cash))


@finance.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
     # Users reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Make sure user entered symbol to buy
        if not request.form.get("symbol"):
            return apology("must provide symbol", 403)

        # Lookup data from API
        elif not lookup(request.form.get("symbol")):
            return apology("company not found", 404)

        # Make sure user entered number of shares to buy
        elif not request.form.get("quantity"):
            return apology("must provide number of shares to buy", 403)

        # Select from table users to see how much money the user has
        userin = Users.query.filter_by(uid=session.get('user_id')).first()

        # Check user's cash with shares to buy
        buyquantity = int(request.form.get("quantity"))
        buylookup = lookup(request.form.get("symbol"))
        if userin.cash < (buylookup["price"]*buyquantity):
            return apology("you don't have enough cash")

        # Insert into stocks table if stock does not exist
        stock = Stocks.query.filter_by(symbol=buylookup["symbol"], name=buylookup["name"]).first()
        if stock is None:
            stockin = Stocks(symbol=buylookup["symbol"], name=buylookup["name"])
            db.session.add(stockin)
            db.session.commit()
            stock = Stocks.query.filter_by(symbol=buylookup["symbol"], name=buylookup["name"]).first()

        # Insert user bought stocks to transactions table
        transac = Transactions(uid=session.get('user_id'), stockid=stock.stockid, transtypeid=1, priceperunit=buylookup["price"], quantity=buyquantity)
        db.session.add(transac)
        db.session.commit()

        # Remove money from user's cash after buying stocks
        userin.cash = float(userin.cash) - (buylookup["price"]*buyquantity)
        db.session.commit()

        # Redirect page to index with flash message
        flash('Bought!')
        return redirect(url_for("finance.index"))

    # Users reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("buy.html")


@finance.route("/history")
@login_required
def history():
    """Show history of transactions"""
    # Lookup in transactions table left joined the stocks table
    query = "SELECT stks.symbol, stks.name, trx.quantity*trx.transtypeid quantity, trx.priceperunit, trx.opdatetime FROM transactions trx LEFT JOIN stocks stks ON trx.stockid = stks.stockid WHERE trx.uid={sesid} ORDER BY opdatetime DESC LIMIT 20".format(sesid=session.get('user_id'))
    transactions = db.engine.execute(query).fetchall()
    return render_template("history.html", transactions=transactions)


@finance.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # Users reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        userin = Users.query.filter_by(name=request.form.get("username")).first()

        # Ensure username exists and password is correct
        if not userin or not check_password_hash(userin.hashpw, request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = userin.uid
        print("Logging in user id: "+str(session.get('user_id')))

        # Redirect user to home page
        return redirect(url_for("finance.index"))

    # Users reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@finance.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.pop('user_id', None)

    # Redirect user to login form
    return redirect(url_for("finance.login"))


@finance.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    # Users reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Make sure user entered symbol for quote
        if not request.form.get("quotesym"):
            return apology("must provide symbol", 403)

        # Lookup data from API
        elif not lookup(request.form.get("quotesym")):
            return apology("company not found", 404)

        # Redirect user to quoted page
        quotelookup = lookup(request.form.get("quotesym"))
        return render_template("quoted.html", name=quotelookup["name"], price=quotelookup["price"], symbol=quotelookup["symbol"])

    # Users reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("quote.html")


@finance.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # Users reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("regusername"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password1"):
            return apology("must provide password", 403)

        # Ensure password was entered again
        elif not request.form.get("password2"):
            return apology("must confirm password", 403)

        # Check database if username exist
        elif Users.query.filter_by(name=request.form.get("regusername")).count() != 0:
            return apology("username exist in database", 409)

        # Check if both passwords matched
        elif request.form.get("password1") != request.form.get("password2"):
            return apology("passwords do not match")

        # Check if password strength is up to requirement
        elif not checkpwstr(request.form.get("password1")):
            return apology("password not up to required strength!")

        # Insert database for username and hashed password
        new_user = Users(name=request.form.get("regusername"), hashpw=generate_password_hash(request.form.get("password1")))
        db.session.add(new_user)
        db.session.commit()

        # Redirect user to home page
        flash('Registered!')
        return redirect(url_for("finance.login"))

    # Users reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@finance.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    # Users reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Make sure user entered symbol to buy
        if not request.form.get("symbol"):
            return apology("must provide symbol", 403)

        # Make sure user entered number of shares to buy
        elif not request.form.get("quantity"):
            return apology("must provide number of shares to sell", 403)

        # Check from stockview to check if selling stock still valid
        stocksown = stockview(session.get('user_id'), symbol=request.form.get("symbol"))
        if stocksown[0]['quantityheld'] < int(request.form.get("quantity")) or len(stocksown) != 1:
            return apology("you don't have sufficient stocks amount")

        # Check current price
        sellquantity = int(request.form.get("quantity"))
        selllookup = lookup(request.form.get("symbol"))

        # Insert into stocks table if stock does not exist
        stock = Stocks.query.filter_by(symbol=selllookup["symbol"], name=selllookup["name"]).first()

        # Insert user sold stocks to transactions table
        transac = Transactions(uid=session.get('user_id'), stockid=stock.stockid, transtypeid=-1, priceperunit=selllookup["price"], quantity=sellquantity)
        db.session.add(transac)
        db.session.commit()

        # Add money to user's cash after buying stocks
        userin = Users.query.filter_by(uid=session.get('user_id')).first()
        userin.cash = float(userin.cash) + (selllookup["price"]*sellquantity)
        db.session.commit()

        # Redirect page to index with flash message
        flash('Sold!')
        return redirect(url_for("finance.index"))

    # Users reached route via GET (as by clicking a link or via redirect)
    else:
        stocksown = stockview(session.get('user_id'))
        return render_template("sell.html", stocks=stocksown)


@finance.route("/changepw", methods=["GET", "POST"])
@login_required
def changepw():
    """Allow user to change their password"""
    # Users reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("oldpassword"):
            return apology("must provide old password", 403)

        # Ensure password was submitted
        elif not request.form.get("password1") or not request.form.get("password2"):
            return apology("must provide new password", 403)

        # Check if both passwords matched
        elif request.form.get("password1") != request.form.get("password2"):
            return apology("passwords do not match")

        # Query database for username
        userin = Users.query.filter_by(uid=session.get('user_id')).first()

        # Ensure password is correct with current session id
        if not userin or not check_password_hash(userin.hashpw, request.form.get("oldpassword")):
            return apology("invalid old password", 403)

        # Update the user table to new password
        userin.hashpw = generate_password_hash(request.form.get("password1"))
        db.session.commit()

        # Redirect user to home page
        flash('Password Successfully Changed!')
        return redirect(url_for("finance.index"))

    # Users reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("changepw.html")


@finance.route("/addcash", methods=["GET", "POST"])
@login_required
def addcash():
    """Allow user to input more cash to the system"""
    # Users reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Make sure user entered symbol for quote
        if not request.form.get("cashadd"):
            return apology("must provide amount", 403)

        # Query database to see the user's cash
        userin = Users.query.filter_by(uid=session.get('user_id')).first()
        userin.cash = float(userin.cash) + float(request.form.get("cashadd"))
        db.session.commit()

        # Redirect user to index page
        flash('Payment Success!')
        return redirect(url_for("finance.index"))

    # Users reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("addcash.html")


def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)

