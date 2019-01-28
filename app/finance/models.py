from datetime import datetime
from app import db
from sqlalchemy.sql import text
from sqlalchemy_views import CreateView

class Users(db.Model):
    __table_args__ = {"schema":"public"}
    uid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    hashpw = db.Column(db.String(120), nullable=False)
    cash = db.Column(db.Numeric(9,2), nullable=False, default=10000)

    def __repr__(self):
        return '<Users %r>' % self.name

class Stocks(db.Model):
    __table_args__ = {"schema":"public"}
    stockid = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(80), unique=True, nullable=False)
    def __repr__(self):
        return '<Stock %r>' % self.symbol

class Transtypes(db.Model):
    __table_args__ = {"schema":"public"}
    tid = db.Column(db.Integer, primary_key=True)
    transid = db.Column(db.Integer, unique=True, nullable=False)
    transtype = db.Column(db.String(80), unique=True, nullable=False)

    def __repr__(self):
        return '<Transtype %r>' % self.transtype

class Transactions(db.Model):
    __table_args__ = {"schema":"public"}
    transacid = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.Integer, db.ForeignKey("public.users.uid"), nullable=False)
    stockid = db.Column(db.Integer, db.ForeignKey("public.stocks.stockid"), nullable=False)
    transtypeid = db.Column(db.Integer, nullable=False)
    priceperunit = db.Column(db.Numeric(9,2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    opdatetime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return '<Transacid %r>' % self.transacid


# Create a view to mine information from transaction table
def createview():
    view = db.Table('v_stockown', db.MetaData(db.engine), schema='public')
    definition = text("SELECT * FROM (SELECT trx.uid, sum(trx.quantity * trx.transtypeid) AS quantityheld, stocks.symbol, stocks.name FROM transactions trx LEFT JOIN stocks stocks ON trx.stockid = stocks.stockid GROUP BY trx.uid, trx.stockid, stocks.symbol, stocks.name) AS prev WHERE prev.quantityheld>0")
    create_view = CreateView(view, definition, or_replace=True)
    db.engine.execute(create_view)
createview()

# Stockview function to ease querying the table
def stockview(userid, **kwargs):
    query = """SELECT * FROM public.v_stockown WHERE uid = {userid}""".format(userid=userid)
    for key in kwargs:
        query += " AND {key} = '{value}'".format(key=key, value=kwargs[key])
    print(query)
    results = db.engine.execute(query)
    rows = results.fetchall()
    return rows
