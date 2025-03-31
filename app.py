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
login_manager.login_view = 'user_login'

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

# CLI command to create admin manually
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

# ------------------- ROUTES ----------------------

@app.route('/')
def index():
    return render_template('index.html')

# ✅ HARD-CODED ADMIN LOGIN
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        # Redirect based on role
        return redirect(url_for('admin_dashboard') if current_user.is_admin else url_for('user_dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        if form.username.data == 'admin' and form.password.data == 'admin123':
            user = User.query.filter_by(username='admin', is_admin=True).first()
            if not user:
                user = User(
                    username='admin',
                    email='admin@example.com',
                    is_admin=True,
                    full_name='Admin User',
                    qualification='Admin',
                    dob=datetime.today()
                )
                user.set_password('admin123')
                db.session.add(user)
                db.session.commit()

            login_user(user)
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid admin credentials", "danger")
    return render_template('auth/admin_login.html', form=form)

# ✅ ADMIN ROUTES
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash("Access denied!", "danger")
        return redirect(url_for('index'))
    return render_template('admin/admin_dash.html', admin=current_user)

@app.route('/admin/quiz')
@login_required
def admin_quiz():
    if not current_user.is_admin:
        flash("Access denied!", "danger")
        return redirect(url_for('index'))
    return render_template('admin/add_quiz.html')

@app.route('/admin/summary')
@login_required
def admin_summary():
    if not current_user.is_admin:
        flash("Access denied!", "danger")
        return redirect(url_for('index'))
    return render_template('admin/summary.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for('admin_login'))

# ✅ USER LOGIN
@app.route('/user/login', methods=['GET', 'POST'])
def user_login():
    if current_user.is_authenticated:
        # Redirect based on role
        return redirect(url_for('admin_dashboard') if current_user.is_admin else url_for('user_dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data, is_admin=False).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid user credentials', 'danger')
            return redirect(url_for('user_login'))

        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('user_dashboard'))

    return render_template('user/user_login.html', form=form)

# ✅ USER REGISTRATION
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter(
            (User.username == form.username.data) | (User.email == form.email.data)
        ).first()
        if existing_user:
            flash("Username or email already exists", "danger")
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
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('user_login'))
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {str(e)}", "danger")

    return render_template('auth/register.html', form=form)

# ✅ USER ROUTES
@app.route('/user/dashboard')
@login_required
def user_dashboard():
    if current_user.is_admin:
        flash("Access denied!", "danger")
        return redirect(url_for('index'))
    return render_template('user/user_dash.html', user=current_user)

@app.route('/user/scores')
@login_required
def scores():
    if current_user.is_admin:
        flash("Access denied!", "danger")
        return redirect(url_for('index'))
    return render_template('user/scores.html')

@app.route('/user/summary')
@login_required
def summary():
    if current_user.is_admin:
        flash("Access denied!", "danger")
        return redirect(url_for('index'))
    return render_template('user/user_summary.html')

# ✅ LOGOUT (shared)
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# ✅ REDIRECT BASED ON ROLE
@app.route('/dashboard')
@login_required
def dashboard():
    # Redirect based on role
    return redirect(url_for('admin_dashboard') if current_user.is_admin else url_for('user_dashboard'))

# ✅ RUN APP
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)