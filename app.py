from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from urllib.parse import urlparse
from datetime import datetime, timedelta

from config import Config
from models import db, User, Subject, Chapter, Quiz, Question, Option, QuizAttempt, UserAnswer
from app.forms import LoginForm, RegistrationForm, SubjectForm, ChapterForm, QuizForm, QuestionForm

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'user_login'  # default if user hits @login_required

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

# Admin user creation CLI remains unchanged
@app.cli.command("create-admin")
def create_admin():
    username = input("Admin username: ")
    email = input("Admin email: ")
    password = input("Admin password: ")
    
    user = User(username=username, email=email, is_admin=True)
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    print(f"Admin user {username} created successfully!")

# Home page
@app.route('/')
def index():
    return render_template('index.html')

# ----------------------------------------
# ✅ LOGIN ROUTES (Split by role)
# ----------------------------------------

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data, is_admin=True).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid admin credentials')
            return redirect(url_for('admin_login'))

        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('admin_dashboard'))

    return render_template('auth/admin_login.html', form=form)


@app.route('/user/login', methods=['GET', 'POST'])
def user_login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data, is_admin=False).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid user credentials')
            return redirect(url_for('user_login'))

        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('user_dashboard'))

    return render_template('user/user_login.html', form=form)

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter((User.username == form.username.data) | (User.email == form.email.data)).first()
        if existing_user:
            flash("Username or email already exists. Please use a different one.", "danger")
            return redirect(url_for('register'))

        try:
            user = User(
                username=form.username.data,
                email=form.email.data,
                full_name=form.full_name.data,
                qualification=form.qualification.data,
                dob=form.dob.data
            )
            user.set_password(form.password.data)

            db.session.add(user)
            db.session.commit()

            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('user_login'))
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {str(e)}", "danger")

    return render_template('auth/register.html', form=form)

# Logout
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

# Dashboard redirect based on role
@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    else:
        return redirect(url_for('user_dashboard'))
    
@app.route('/user/dashboard')
@login_required
def user_dashboard():
    return render_template('user/user_dash.html', user=current_user)

@app.route('/user/scores')
@login_required
def scores():
    return render_template('user/scores.html')

@app.route('/user/summary')
@login_required
def summary():
    return render_template('user/user_summary.html')



# ✅ MAIN ENTRY POINT TO RUN FLASK APP
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensures tables are created before first request
    app.run(debug=True)
