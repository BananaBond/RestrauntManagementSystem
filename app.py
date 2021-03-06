import sqlite3, os
from flask import Flask, flash, redirect, render_template, request, session, abort, g, url_for, jsonify
from passlib.hash import sha256_crypt as sha
from hashlib import md5
from functools import wraps
from datetime import datetime
from wtforms import Form, BooleanField, StringField, PasswordField, validators,TextAreaField,IntegerField
import numpy as np

app = Flask(__name__, static_url_path="", static_folder="static")

app.secret_key = os.urandom(12)
Database = 'MainDatabase.db'


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("username") is None:
            flash(" Please login ",'danger')

            return redirect(url_for("login",user=session.get("username"), next=request.url))
        return f(*args, **kwargs)

    return decorated_function
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if (session.get("usertype") !="admin"):
            return redirect(url_for("index",user=session.get("username"), next=request.url))
        return f(*args, **kwargs)

    return decorated_function


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(Database)
    return db


def query_db(query, args=(), one=False):  # used to retrieve values from the table
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


def execute_db(query, args=()):  # executes a sql command like alter table and insert
    conn = get_db()
    cur = conn.cursor()
    cur.execute(query, args)
    conn.commit()
    cur.close()

class ReservationForm(Form):
    firstname=StringField('First Name',[validators.Length(min=2,max=25),validators.required()])
    lastname=StringField('First Name',[validators.Length(min=2,max=25)])
    email=StringField('Email',[validators.Email,validators.required()])
    time=IntegerField('Time',[validators.required()])
    seats=IntegerField('Number of seats',[validators.required()])
    address=StringField('Address',[validators.required()])
    message=TextAreaField('Message for the chef',[validators.optional(),validators.Length(max=200)])
    accept_tos=BooleanField('I accept TOS',[validators.DataRequired()])


@app.route('/')
def index():
    if(session.get("usertype")!="admin"):
        return render_template('index.html',user=session.get("username"),)
    if(session.get("usertype")=="admin"):
        return render_template('admin_index.html',user=session.get("username"))
@app.route('/about')
def about():
    return render_template('about.html',user=session.get("username"))

@app.route('/menu')
def menu():
    data = query_db("select name,category,description,option1,option2,option3,price1,price2,price3 from menu")
    return render_template('menu.html',user=session.get("username"),alldata=data)





@app.route('/team')
def team():
    return render_template('team.html',user=session.get("username"))

@app.route('/reservation',methods=['POST','GET'])
def reservation():
#     form=ReservationForm(request.form)
#     if query_db("select firstname from Reservations where firstname = ?",( form.firstname.data,)):
#         if(query_db("select lastname from Reservations where lastname = ?",( form.lastname.data,))):
#
#             ("User already taken","danger")
#         return render_template("reservation.html",form=form)
#     if request.method == 'POST' and form.validate():
#         password = sha.encrypt(form.password.data)
#         execute_db("insert into Reservations values(?,?,?,?,?,?)", (form.firstname.data,form.lastname.data,form.email.data,form.time,form.seats.data,form.message.data,))
#         flash('Thanks for your reservation')
#         return redirect(url_for('index'))
    if request.method=="GET":
        return render_template('reservation.html',user=session.get("username"))
    else:
        submission ={}
        submission["firstname"]=request.form["firstname"]
        submission["lastname"]=request.form["lastname"]
        submission["email"]=request.form["email"]
        submission["time"]=request.form["time"]
        submission["address"]=request.form["address"]
        submission["city"]=request.form["city"]
        submission['notes']=request.form['notes']
        submission['seats']=request.form['seats']

        execute_db("insert into reservations values(?,?,?,?,?,?,?,?)", (
        submission["firstname"],
        submission["lastname"],
        submission["email"],
        submission["time"],
        submission["address"],
        submission["city"],
        submission['notes'],
        submission['seats']
        ))
    flash(" Reservation created ","success")
    return render_template('reservation.html',user=session.get("username"))


@app.route('/contact')
def contact():
    return render_template('contact.html',user=session.get("username"))

@app.route('/elements')
def elements():
    return render_template('elements.html')

@app.route('/cart')
@login_required
def cart():

    data = query_db("select customername,item from cart where customername=?",(session["username"],))


    return render_template('/cart.html',user=session.get("username"),alldata=data)


@app.route('/admin_reservation')
@admin_required
def admin_reservation():

    data=query_db("select firstname,lastname,seats,time,email from reservations")
    return render_template('admin_reservation.html',user=session.get("username"),alldata=data)

@app.route('/admin_orders')
@admin_required
def admin_orders():
    data = query_db("select orderid,customername,item,amount from orders")
    return render_template('orders.html',user=session.get("username"),alldata=data)

@app.route('/login',methods=['POST','GET'])
def login():
    if request.method == "GET":
        return render_template("login.html",user=session.get("username"))
    else:
        error = None
        username = request.form["username"]
        password = request.form["password"]

        passdatabase = query_db("select password from users where username = ?", (username,))
        if passdatabase == []:
            flash(" User does not exist ", "danger")
            return render_template("login.html",user=session.get("username"))
        usertype=query_db("select usertype from users where username = ?", (username,))

        if  (sha.verify(password,passdatabase[0][0])):
            flash(" Login successful ","success")
            session["username"] = username
            session["usertype"]=usertype[0][0]
            return redirect(url_for('index'))
        else:
            flash( " Incorrect Password ", "danger")
            return render_template("login.html",user=session.get("username"))
@app.route('/admin_register',methods=['POST','GET'])
def admin_register():
    if request.method=="GET":
        return render_template('admin_register.html',user=session.get("username"))
    else:
        submission = {}
        submission["email"] = request.form["email"]

        submission["password"] = request.form["password"]
        submission["conf_pass"] = request.form["conf_pass"]
        usertype="admin"
        if submission["password"] != submission["conf_pass"]:
            flash("Passwords don't match", "danger")
            return render_template("admin_register.html",user=session.get("username"))

        if query_db("select username from users where username = ?", (submission["email"],)) != []:
            flash("Email already taken", "danger")
            return render_template("admin_register.html",user=session.get("username"))

        password = sha.encrypt(submission["password"])
        uid=100000000*np.random.random()
        uid=int(uid)

        execute_db("insert into users values(?,?,?,?)", (
            uid,
            submission["email"],

            password,
            usertype
        ))

        flash(" User Created ", "success")
    return redirect(url_for("login"))

@app.route('/register',methods=['POST','GET'])
def register():
    if request.method=="GET":
        return render_template('register.html',user=session.get("username"))
    else:
        submission = {}
        submission["email"] = request.form["email"]
        submission["firstname"]=request.form["firstname"]
        submission["lastname"] = request.form["lastname"]
        submission["address"] = request.form["address"]
        submission["contact"]=request.form["contact"]
        submission["password"] = request.form["password"]
        submission["conf_pass"] = request.form["conf_pass"]
        usertype="customer"
        if submission["password"] != submission["conf_pass"]:
            flash("Passwords don't match", "danger")
            return render_template("register.html",user=session.get("username"))

        if query_db("select username from users where username = ?", (submission["email"],)) != []:
            flash("Email already taken", "danger")
            return render_template("register.html",user=session.get("username"))

        password = sha.encrypt(submission["password"])
        uid=100000000*np.random.random()
        uid=int(uid)

        execute_db("insert into users values(?,?,?,?)", (
            uid,
            submission["email"],

            password,
            usertype
        ))
        execute_db("insert into customers values(?,?,?,?,?,?)",(
            uid,
            submission["firstname"],
            submission["lastname"],
            submission["email"],
            submission["contact"],
            submission["address"]
        ))
        flash(" User Created ", "success")
    return redirect(url_for("login"))
@app.route('/logout')
def logout():
    session.clear()
    flash(" Logout successful ", "success")
    return redirect(url_for('login'))

@app.route('/addtocart/<name>/<size>/<option>')
@login_required
def addtocart(name,size,option):
    itemname=name
    pid=query_db("select ProductID from menu where name=?",(itemname,))
    itemsize=size
    code=itemname+" "+itemsize
    writeoption=option

    customername=session["username"]
    uid = query_db("select uid from users where username=?",(customername,))
    execute_db("insert into cart values(?,?,?,?)", (
       customername, code, pid[0][0], writeoption
    ))
    flash(" Added to cart "+code,"success")
    return redirect(url_for('menu'))
@app.route('/place_order')
@login_required
def place_order():
    oid = 100000000 * np.random.random()
    oid = int(oid)
    itemlist=""
    curretuser=session.get("username")
    amount=0
    lists=query_db("select item, pid,option from cart where customername=?",(curretuser,))

    for i in lists:
        curr_itemname=i[0]
        curr_pid=i[1]
        curr_option=i[2]
        if curr_option==1:
            cost = query_db("select price1 from menu where ProductID=? ", (curr_pid,))
        elif curr_option==2:
            cost = query_db("select price2 from menu where ProductID=? ", (curr_pid,))
        elif curr_option==3:
            cost = query_db("select price3 from menu where ProductID=? ", (curr_pid,))


        itemlist+=i[0]+", "
        amount+=cost[0][0]
    execute_db("insert into orders values(?,?,?,?)",(oid,curretuser,itemlist,amount))
    flash("Order placed ","success")

    execute_db("delete from cart where customername=?",(curretuser,))
    return redirect(url_for('index'))


@app.route('/employee')
def employee():
    data = query_db("select name,designation,image from employees ")
    return render_template('team.html',user=session.get("username"),alldata=data)

@app.route('/layout')
def layout():
    return render_template('layout.html')
@app.route("/profile")
@login_required
def profile():
    currentuser=session.get("username")
    data=query_db("select username from users where username = ?",(currentuser,))

    return render_template('profile.html',data=data)

app
if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=80)
