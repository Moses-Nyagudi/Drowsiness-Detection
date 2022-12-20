from urllib import response
from flask import Flask, render_template, request, redirect, url_for, session
from keras.models import load_model
from flask_mysqldb import MySQL
from flask import make_response
from flask_session import Session
import MySQLdb.cursors
import pyaudio
import numpy as np
import winsound
import re
import cv2
app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

blinks = []
perclos = []
Labels = []

# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = 'A1B2C3D4#hash'

# Enter your database connection details below
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'pythonlogin'

# Intialize MySQL
mysql = MySQL(app)

# http://localhost:5000/pythonlogin/ - the following will be our login page, which will use both GET and POST requests
@app.route('/')
@app.route('/pythonlogin/', methods=['GET', 'POST'])
def login():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password,))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            # Redirect to home page
            return redirect(url_for('home'))
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    # Show the login form with message (if any)
    return render_template('index.html', msg=msg)

# http://localhost:5000/python/logout - this will be the logout page
@app.route('/pythonlogin/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   # Redirect to login page
   return redirect(url_for('login'))

# http://localhost:5000/pythinlogin/register - this will be the registration page, we need to use both GET and POST requests
@app.route('/pythonlogin/register', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ' '
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
    
                # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s)', (username, password, email,))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
    elif request.method == 'POST': 
         # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('register.html', msg=msg)
                

# http://localhost:5000/pythinlogin/home - this will be the home page, only accessible for loggedin users
@app.route('/pythonlogin/home')
def home():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        return render_template('home.html', username=session['username'])
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

# http://localhost:5000/pythinlogin/profile - this will be the profile page, only accessible for loggedin users
@app.route('/pythonlogin/profile')
def profile():
    # Check if user is loggedin
    if 'loggedin' in session:
        # We need all the account info for the user so we can display it on the profile page
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
        account = cursor.fetchone()
        # Show the profile page with account info
        return render_template('profile.html', account=account)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

# http://localhost:5000/pythinlogin/profile - this will be the profile page, only accessible for loggedin users

# Load the CNN model
model = load_model('drowsiness_new.h5')

@app.route('/turn_on_camera')
def turn_on_camera():
    # Open the default camera
    cap = cv2.VideoCapture(0)
    
    # Check if the camera is opened successfully
    if not cap.isOpened():
        print("Error opening camera")
        return

    # Run the camera until the user closes it
    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()

        # Check if the frame was read successfully
        if not ret:
            print("Error reading frame")
            continue

        # Preprocess the frame to match the input shape of the CNN model
        frame = cv2.resize(frame, (145, 145))
        frame = np.expand_dims(frame, axis=0)
        frame = frame / 255.0

        # Pass the frame to the CNN model to make a prediction
        prediction = model.predict(frame)

        # If the prediction is that the eyes are closed, trigger an alarm
        if prediction == (1,2):
            pyaudio.play_sound('alarm.mp3')
            winsound.PlaySound('alarm.mp3', winsound.SND_FILENAME)

        # Display the resulting frame
        cv2.imshow('Camera', frame)

        # Press q on the keyboard to exit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # When everything is done, release the capture
    cap.release()
    cv2.destroyAllWindows()

@app.route('/turn_off_camera', methods=['POST'])
def turn_off_camera():
    # Open the default camera
    cap = cv2.VideoCapture(0)

    # Check if the camera is opened successfully
    if not cap.isOpened():
        print("Error opening camera")
        return

    # Run the camera until the user closes it
    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()

        # Check if the frame was read successfully
        if not ret:
            print("Error reading frame")
            continue

        # Display the raw frame from the camera
        cv2.imshow('Camera', frame)

        # Press q on the keyboard to exit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # When everything is done, release the capture and close any open windows
    cap.release()
    cv2.destroyAllWindows()




      


