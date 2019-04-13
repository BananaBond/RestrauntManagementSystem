import sqlite3, os
from flask import Flask, flash, redirect, render_template, request, session, abort, g, url_for, jsonify
from passlib.hash import sha256_crypt as sha
from hashlib import md5
from functools import wraps
from datetime import datetime
from wtforms import Form, BooleanField, StringField, PasswordField, validators,TextAreaField,IntegerField


app = Flask(__name__, static_url_path="", static_folder="static")

app.secret_key = os.urandom(12)
Database = 'MainDatabase.db'


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("username") is None:
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)

    return decorated_function
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if (session.get("usertype") !="admin"):
            return redirect(url_for("index", next=request.url))
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
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/menu')

def menu():
    return render_template('menu.html')
@app.route('/team')
def team():
    return render_template('team.html')

@app.route('/reservation',methods=['POST','GET'])
def reservation():
#     form=ReservationForm(request.form)
#     if query_db("select firstname from Reservations where firstname = ?",( form.firstname.data,)):
#         if(query_db("select lastname from Reservations where lastname = ?",( form.lastname.data,))):
#             flash("User already taken","danger")
#         return render_template("reservation.html",form=form)
#     if request.method == 'POST' and form.validate():
#         password = sha.encrypt(form.password.data)
#         execute_db("insert into Reservations values(?,?,?,?,?,?)", (form.firstname.data,form.lastname.data,form.email.data,form.time,form.seats.data,form.message.data,))
#         flash('Thanks for your reservation')
#         return redirect(url_for('index'))
    if request.method=="GET":
        return render_template('reservation.html')
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
    flash("Reservation created","success")
    return render_template('reservation.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/elements')
def elements():
    return render_template('elements.html')

@app.route('/admin_reservation')
@admin_required
def admin_reservation():
    flash("Welcome Admin","success")
    data=query_db("select firstname,lastname,seats,time,email from reservations")
    return render_template('admin_reservation.html',alldata=data)

@app.route('/login',methods=['POST','GET'])
def login():
    if request.method == "GET":
        return render_template("login.html")
    else:
        error = None
        username = request.form["username"]
        password = request.form["password"]

        passdatabase = query_db("select password from users where username = ?", (username,))
        if passdatabase == "":
            flash("User does not exist", "danger")
            return render_template("login.html")
        usertype=query_db("select usertype from users where username = ?", (username,))
        if (sha.verify(password,passdatabase[0][0])):
            flash("Login Successful","success")
            session["username"] = username
            session["usertype"]=usertype[0][0]
            return redirect(url_for('index'))
        else:
            flash("Incorrect Password", "danger")
            return render_template("login.html")

@app.route('/register',methods=['POST','GET'])
def register():
    if request.method=="GET":
        return render_template('register.html')
    else:
        submission = {}
        submission["username"] = request.form["username"]

        submission["password"] = request.form["password"]
        submission["conf_pass"] = request.form["conf_pass"]
        submission["usertype"]=request.form["usertype"]
        if submission["password"] != submission["conf_pass"]:
            flash("Passwords don't match", "danger")
            return render_template("register.html")

        if query_db("select username from users where username = ?", (submission["username"],)) != []:
            flash("User already taken", "danger")
            return render_template("register.html")

        password = sha.encrypt(submission["password"])
        execute_db("insert into users values(?,?,?)", (
            submission["username"],

            password,
            submission["usertype"]
        ))
        flash("User Created", "success")
    return redirect(url_for("login"))

app
if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=80)
