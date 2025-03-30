from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
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
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

# Create admin user command
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

# Route for home page
@app.route('/')
def index():
    return render_template('index.html')

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            if user.is_admin:
                next_page = url_for('admin_dashboard')
            else:
                next_page = url_for('user_dashboard')
        return redirect(next_page)
    
    return render_template('auth/login.html', form=form)

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
                dob=form.dob.data  # Ensure this matches your form field name
            )
            user.set_password(form.password.data)

            db.session.add(user)
            db.session.commit()

            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {str(e)}", "danger")
    
    return render_template('auth/register.html', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

# Dashboard routes
@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    else:
        return redirect(url_for('user_dashboard'))

# Admin routes
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied: Admin privileges required')
        return redirect(url_for('user_dashboard'))
    
    subjects = Subject.query.count()
    chapters = Chapter.query.count()
    quizzes = Quiz.query.count()
    users = User.query.filter_by(is_admin=False).count()
    
    return render_template('admin/dashboard.html', 
                          subjects=subjects,
                          chapters=chapters,
                          quizzes=quizzes,
                          users=users)

# Subject management routes
@app.route('/admin/subjects', methods=['GET', 'POST'])
@login_required
def manage_subjects():
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('user_dashboard'))
    
    form = SubjectForm()
    if form.validate_on_submit():
        subject = Subject(name=form.name.data, description=form.description.data)
        db.session.add(subject)
        db.session.commit()
        flash('Subject added successfully!')
        return redirect(url_for('manage_subjects'))
    
    subjects = Subject.query.all()
    return render_template('admin/subjects.html', subjects=subjects, form=form)

# Chapter management routes
@app.route('/admin/chapters', methods=['GET', 'POST'])
@login_required
def manage_chapters():
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('user_dashboard'))
    
    form = ChapterForm()
    form.subject_id.choices = [(s.id, s.name) for s in Subject.query.all()]
    
    if form.validate_on_submit():
        chapter = Chapter(
            title=form.title.data,
            description=form.description.data,
            subject_id=form.subject_id.data
        )
        db.session.add(chapter)
        db.session.commit()
        flash('Chapter added successfully!')
        return redirect(url_for('manage_chapters'))
    
    chapters = Chapter.query.all()
    return render_template('admin/chapters.html', chapters=chapters, form=form)

# Quiz management routes
@app.route('/admin/quizzes', methods=['GET', 'POST'])
@login_required
def manage_quizzes():
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('user_dashboard'))
    
    form = QuizForm()
    form.chapter_id.choices = [(c.id, f"{c.subject.name} - {c.title}") for c in Chapter.query.all()]
    
    if form.validate_on_submit():
        quiz = Quiz(
            title=form.title.data,
            description=form.description.data,
            duration_minutes=form.duration_minutes.data,
            chapter_id=form.chapter_id.data
        )
        db.session.add(quiz)
        db.session.commit()
        flash('Quiz created successfully!')
        return redirect(url_for('edit_quiz', quiz_id=quiz.id))
    
    quizzes = Quiz.query.all()
    return render_template('admin/quizzes.html', quizzes=quizzes, form=form)

@app.route('/admin/quizzes/<int:quiz_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_quiz(quiz_id):
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('user_dashboard'))
    
    quiz = Quiz.query.get_or_404(quiz_id)
    form = QuestionForm()
    
    if form.validate_on_submit():
        question = Question(question_text=form.question_text.data, quiz=quiz)
        db.session.add(question)
        db.session.flush()  # Get the question ID
        
        for i, option_text in enumerate([
            form.option_a.data, form.option_b.data, 
            form.option_c.data, form.option_d.data
        ]):
            option = Option(
                option_text=option_text,
                is_correct=(i+1 == form.correct_option.data),
                question=question
            )
            db.session.add(option)
        
        db.session.commit()
        flash('Question added successfully!')
        return redirect(url_for('edit_quiz', quiz_id=quiz_id))
    
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    return render_template('admin/edit_quiz.html', quiz=quiz, questions=questions, form=form)

# User routes
@app.route('/user/dashboard')
@login_required
def user_dashboard():
    quizzes = Quiz.query.all()  # Fetch all quizzes or specific quizzes based on user
    return render_template('user/dashboard.html', quizzes=quizzes)  # Pass quizzes list
    
    # Get completed quizzes with scores
    completed_attempts = QuizAttempt.query.filter_by(
        user_id=current_user.id
    ).filter(
        QuizAttempt.end_time.isnot(None)
    ).all()
    
    # Get active quiz attempt if any
    active_attempt = QuizAttempt.query.filter_by(
        user_id=current_user.id,
        end_time=None
    ).first()
    
    # Prepare data for charts
    subjects = Subject.query.all()
    subject_scores = []
    for subject in subjects:
        # Calculate average score for each subject
        subject_quizzes = []
        for chapter in subject.chapters:
            subject_quizzes.extend(chapter.quizzes.all())
        
        total_score = 0
        count = 0
        for quiz in subject_quizzes:
            attempts = QuizAttempt.query.filter_by(
                user_id=current_user.id,
                quiz_id=quiz.id,
                end_time=not None
            ).all()
            
            for attempt in attempts:
                if attempt.score is not None:
                    total_score += attempt.score_percentage
                    count += 1
        
        avg_score = total_score / count if count > 0 else 0
        subject_scores.append({
            'name': subject.name,
            'score': avg_score
        })
    
    # Get monthly attempt counts
    monthly_data = []
    now = datetime.utcnow()
    for i in range(6):
        month_start = datetime(now.year, now.month - i if now.month - i > 0 else now.month - i + 12, 1)
        month_end = datetime(month_start.year, month_start.month + 1 if month_start.month < 12 else 1, 1)
        
        count = QuizAttempt.query.filter_by(user_id=current_user.id).filter(
            QuizAttempt.start_time >= month_start,
            QuizAttempt.start_time < month_end
        ).count()
        
        monthly_data.append({
            'month': month_start.strftime('%b'),
            'count': count
        })
    
    # Current question if in active attempt
    current_question = None
    if active_attempt:
        # Get the next unanswered question
        answered_questions = UserAnswer.query.filter_by(attempt_id=active_attempt.id).with_entities(UserAnswer.question_id).all()
        answered_ids = [q.question_id for q in answered_questions]
        
        questions = Question.query.filter_by(quiz_id=active_attempt.quiz_id).all()
        unanswered = [q for q in questions if q.id not in answered_ids]
        
        if unanswered:
            current_question = unanswered[0]
            options = Option.query.filter_by(question_id=current_question.id).all()
            current_question.options = options
    
    return render_template('user/dashboard.html',
                          upcoming_quizzes=upcoming_quizzes,
                          completed_attempts=completed_attempts,
                          active_attempt=active_attempt,
                          current_question=current_question,
                          subject_scores=subject_scores,
                          monthly_data=monthly_data)

@app.route('/user/quizzes')
@login_required
def available_quizzes():
    quizzes = Quiz.query.filter_by(active=True).all()
    return render_template('user/available_quizzes.html', quizzes=quizzes)

@app.route('/user/quiz/<int:quiz_id>/view')
@login_required
def view_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    return render_template('user/view_quiz.html', quiz=quiz)

@app.route('/user/quiz/<int:quiz_id>/start')
@login_required
def start_quiz(quiz_id):
    # Check if there's an active attempt
    active_attempt = QuizAttempt.query.filter_by(
        user_id=current_user.id,
        quiz_id=quiz_id,
        end_time=None
    ).first()
    
    if not active_attempt:
        # Create new attempt
        active_attempt = QuizAttempt(
            user_id=current_user.id,
            quiz_id=quiz_id,
            start_time=datetime.utcnow()
        )
        db.session.add(active_attempt)
        db.session.commit()
    
    return redirect(url_for('take_quiz', attempt_id=active_attempt.id))

@app.route('/user/attempt/<int:attempt_id>/question', methods=['GET', 'POST'])
@login_required
def take_quiz(attempt_id):
    attempt = QuizAttempt.query.get_or_404(attempt_id)
    
    # Security check
    if attempt.user_id != current_user.id:
        flash('Access denied')
        return redirect(url_for('user_dashboard'))
    
    # Check if attempt is expired
    quiz = attempt.quiz
    if datetime.utcnow() > attempt.start_time + timedelta(minutes=quiz.duration_minutes):
        if not attempt.end_time:
            attempt.end_time = attempt.start_time + timedelta(minutes=quiz.duration_minutes)
            db.session.commit()
        flash('This quiz attempt has expired')
        return redirect(url_for('user_dashboard'))
    
    # Handle answer submission
    if request.method == 'POST':
        question_id = request.form.get('question_id')
        option_id = request.form.get('option_id')
        
        if question_id and option_id:
            # Check if already answered
            existing_answer = UserAnswer.query.filter_by(
                attempt_id=attempt_id,
                question_id=question_id
            ).first()
            
            if existing_answer:
                existing_answer.selected_option_id = option_id
            else:
                answer = UserAnswer(
                    attempt_id=attempt_id,
                    question_id=question_id,
                    selected_option_id=option_id
                )
                db.session.add(answer)
            
            db.session.commit()
            
            # Check if all questions answered
            submit = request.form.get('submit')
            if submit:
                return calculate_score(attempt_id)
            
    # Get next unanswered question
    answered = UserAnswer.query.filter_by(attempt_id=attempt_id).with_entities(UserAnswer.question_id).all()
    answered_ids = [a.question_id for a in answered]
    
    all_questions = Question.query.filter_by(quiz_id=quiz.id).all()
    unanswered = [q for q in all_questions if q.id not in answered_ids]
    
    if not unanswered:
        # All questions answered
        return calculate_score(attempt_id)
    
    current_question = unanswered[0]
    options = Option.query.filter_by(question_id=current_question.id).all()
    
    time_left = int((attempt.start_time + timedelta(minutes=quiz.duration_minutes) - datetime.utcnow()).total_seconds())
    
    return render_template('user/take_quiz.html',
                          attempt=attempt,
                          question=current_question,
                          options=options,
                          question_num=len(answered_ids) + 1,
                          total_questions=len(all_questions),
                          time_left=time_left)

def calculate_score(attempt_id):
    attempt = QuizAttempt.query.get_or_404(attempt_id)
    
    # Already calculated
    if attempt.score is not None and attempt.end_time is not None:
        return redirect(url_for('quiz_results', attempt_id=attempt_id))
    
    # Calculate score
    score = 0
    total_questions = Question.query.filter_by(quiz_id=attempt.quiz_id).count()
    
    for answer in attempt.answers:
        option = Option.query.get(answer.selected_option_id)
        if option and option.is_correct:
            score += 1
    
    attempt.score = score
    attempt.end_time = datetime.utcnow()
    db.session.commit()
    
    return redirect(url_for('quiz_results', attempt_id=attempt_id))

@app.route('/user/attempt/<int:attempt_id>/results')
@login_required
def quiz_results(attempt_id):
    attempt = QuizAttempt.query.get_or_404(attempt_id)
    
    # Security check
    if attempt.user_id != current_user.id:
        flash('Access denied')
        return redirect(url_for('user_dashboard'))
    
    # Get all questions with answers
    questions = Question.query.filter_by(quiz_id=attempt.quiz_id).all()
    
    # Get user answers
    user_answers = {a.question_id: a.selected_option_id for a in attempt.answers}
    
    # Get correct answers
    correct_answers = {}
    for question in questions:
        for option in question.options:
            if option.is_correct:
                correct_answers[question.id] = option.id
    
    return render_template('user/quiz_results.html',
                          attempt=attempt,
                          questions=questions,
                          user_answers=user_answers,
                          correct_answers=correct_answers)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)