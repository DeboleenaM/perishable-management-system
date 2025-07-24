from flask import Blueprint, render_template, request, redirect, url_for, session

auth = Blueprint('auth', __name__)

@auth.route('/')
def home():
    return redirect(url_for('auth.login'))

@auth.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        session['username'] = username
        return redirect(url_for('main.dashboard'))
    return '''
        <form method="POST">
            Username: <input type="text" name="username"><br>
            <input type="submit" value="Login">
        </form>
    '''

@auth.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
