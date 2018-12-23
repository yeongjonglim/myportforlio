import os

# from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

from financeHelpers import apology, login_required, lookup, usd, checkpwstr

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
# db = SQL("sqlite:///finance.db")

# Change configuration to connect to new database (SQLAchemy)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    hashpw = db.Column(db.String(120), nullable=False)
    cash = db.Column(db.Numeric, nullable=False, default=10000)

    def __repr__(self):
        return '<User %r>' % self.name


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    # Query database for what the user currently has
    # stocksowned = db.execute("SELECT * FROM v_stockown WHERE userid = :sesid", sesid=session.get('user_id'))
    # userval = db.execute("SELECT * FROM users WHERE id = :sesid", sesid=session.get('user_id'))

    # Lookup for stocks' current price
    # indlookup = []
    # for stock in stocksowned:
    #    indlookup.append(lookup(stock["symbol"]))
    # return render_template("index.html", stocksinfo=indlookup, stocksowned=stocksowned, usercash=userval[0]["cash"])
    return apology("TODO")


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
     # User reached route via POST (as by submitting a form via POST)
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
        user = db.execute("SELECT * FROM users WHERE id = :sesid", sesid=session.get('user_id'))

        # Check user's cash with shares to buy
        buyquantity = int(request.form.get("quantity"))
        buylookup = lookup(request.form.get("symbol"))
        if user[0]['cash'] < (buylookup["price"]*buyquantity):
            return apology("you don't have enough cash")

        # Insert into stocks table if stock does not exist
        stock = db.execute("SELECT * FROM stocks WHERE symbol=:sym AND name=:name", sym=buylookup["symbol"], name=buylookup["name"])
        if len(stock) != 1:
            db.execute("INSERT INTO stocks (symbol, name) VALUES (:sym, :name)", sym=buylookup["symbol"], name=buylookup["name"])
            stock = db.execute("SELECT * FROM stocks WHERE symbol=:sym AND name=:name", sym=buylookup["symbol"], name=buylookup["name"])

        # Insert user bought stocks to transactions table
        db.execute("INSERT INTO transactions (userid, stockid, transtypeid, priceperunit, quantity) VALUES (:sesid, :stockid, :transtype, :price, :quantity)",
                    sesid=session.get('user_id'), stockid=int(stock[0]['stockid']), transtype=1, price=buylookup["price"], quantity=buyquantity)

        # Remove money from user's cash after buying stocks
        usernewcash = user[0]['cash'] - (buylookup["price"]*buyquantity)
        db.execute("UPDATE users SET cash=:updatedcash WHERE id=:sesid", updatedcash=usernewcash, sesid=session.get('user_id'))

        # Redirect page to index with flash message
        flash('Bought!')
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    # Lookup in transactions table left joined the stocks table
    transactions = db.execute("SELECT stks.symbol, stks.name, trx.quantity*trx.transtypeid quantity, trx.priceperunit, trx.opdatetime FROM transactions trx LEFT JOIN stocks stks ON trx.stockid = stks.stockid WHERE trx.userid=:sesid", sesid=session.get('user_id'))
    return render_template("history.html", transactions=transactions)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        # rows = db.execute("SELECT * FROM users WHERE username = :username",
        #                  username=request.form.get("username"))
        user = User.query.filter_by(username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(user) != 1 or not check_password_hash(user[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/login")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    # User reached route via POST (as by submitting a form via POST)
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

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # User reached route via POST (as by submitting a form via POST)
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
        elif len(User.query.filter_by(request.form.get("regusername"))) != 0:
            return apology("username exist in database", 409)

        # Check if both passwords matched
        elif request.form.get("password1") != request.form.get("password2"):
            return apology("passwords do not match")

        # Check if password strength is up to requirement
        elif not checkpwstr(request.form.get("password1")):
            return apology("password not up to required strength!")

        # Insert database for username and hashed password
        # db.execute("INSERT INTO users (username, hash) VALUES (:regusername, :hashpassword)",
        #            regusername=request.form.get("regusername"), hashpassword=generate_password_hash(request.form.get("password1")))
        new_user = User(request.form.get("regusername"), generate_password_hash(request.form.get("password1")))
        db.session.add(new_user)
        db.session.commit()

        # Redirect user to home page
        return redirect("/login")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Make sure user entered symbol to buy
        if not request.form.get("symbol"):
            return apology("must provide symbol", 403)

        # Make sure user entered number of shares to buy
        elif not request.form.get("quantity"):
            return apology("must provide number of shares to sell", 403)

        # Check from stockview to check if selling stock still valid
        stocksowned = db.execute("SELECT * FROM v_stockown WHERE userid = :sesid AND symbol = :symbol", sesid=session.get('user_id'), symbol=request.form.get("symbol"))
        if stocksowned[0]["quantityheld"] < int(request.form.get("quantity")) or len(stocksowned) != 1:
            return apology("you don't have sufficient stocks amount")

        # Check current price
        sellquantity = int(request.form.get("quantity"))
        selllookup = lookup(request.form.get("symbol"))

        # Insert into stocks table if stock does not exist
        stock = db.execute("SELECT * FROM stocks WHERE symbol=:sym AND name=:name", sym=selllookup["symbol"], name=selllookup["name"])

        # Insert user sold stocks to transactions table
        db.execute("INSERT INTO transactions (userid, stockid, transtypeid, priceperunit, quantity) VALUES (:sesid, :stockid, :transtype, :price, :quantity)",
                    sesid=session.get('user_id'), stockid=int(stock[0]['stockid']), transtype=-1, price=selllookup["price"], quantity=sellquantity)

        # Add money to user's cash after buying stocks
        user = db.execute("SELECT * FROM users WHERE id = :sesid", sesid=session.get('user_id'))
        usernewcash = user[0]['cash'] + (selllookup["price"]*sellquantity)
        db.execute("UPDATE users SET cash=:updatedcash WHERE id=:sesid", updatedcash=usernewcash, sesid=session.get('user_id'))

        # Redirect page to index with flash message
        flash('Sold!')
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        stocksowned = db.execute("SELECT * FROM v_stockown WHERE userid = :sesid", sesid=session.get('user_id'))
        return render_template("sell.html", stocks=stocksowned)


@app.route("/changepw", methods=["GET", "POST"])
@login_required
def changepw():
    """Allow user to change their password"""
    # User reached route via POST (as by submitting a form via POST)
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
        user = db.execute("SELECT * FROM users WHERE id = :sesid", sesid=session.get('user_id'))

        # Ensure password is correct with current session id
        if len(user) != 1 or not check_password_hash(user[0]["hash"], request.form.get("oldpassword")):
            return apology("invalid old password", 403)

        # Update the user table to new password
        db.execute("UPDATE users SET hash=:newpassword WHERE id=:sesid", newpassword=generate_password_hash(request.form.get("password1"), sesid=session.get('user_id')))

        # Redirect user to home page
        flash('Password Successfully Changed!')
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("changepw.html")


@app.route("/addcash", methods=["GET", "POST"])
@login_required
def addcash():
    """Allow user to input more cash to the system"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Make sure user entered symbol for quote
        if not request.form.get("cashadd"):
            return apology("must provide amount", 403)

        # Query database to see the user's cash
        user = db.execute("SELECT * FROM users WHERE id = :sesid", sesid=session.get('user_id'))
        usernewcash = user[0]['cash'] + float(request.form.get("cashadd"))
        db.execute("UPDATE users SET cash=:updatedcash WHERE id=:sesid", updatedcash=usernewcash, sesid=session.get('user_id'))

        # Redirect user to index page
        flash('Payment Success!')
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("addcash.html")


def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
