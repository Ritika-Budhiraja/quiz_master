from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, Subject, Chapter, Quiz, Question, User, Score
from forms import SubjectForm, ChapterForm, QuizForm, QuestionForm, SearchForm
from functools import wraps
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Admin access required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Count statistics for dashboard
    users_count = User.query.filter_by(is_admin=False).count()
    subjects_count = Subject.query.count()
    chapters_count = Chapter.query.count()
    quizzes_count = Quiz.query.count()
    
    # Get recent quizzes
    recent_quizzes = Quiz.query.order_by(Quiz.date_of_quiz.desc()).limit(5).all()
    
    # Get recent user registrations
    recent_users = User.query.filter_by(is_admin=False).order_by(User.id.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                           users_count=users_count,
                           subjects_count=subjects_count,
                           chapters_count=chapters_count,
                           quizzes_count=quizzes_count,
                           recent_quizzes=recent_quizzes,
                           recent_users=recent_users)

# Subject Management
@admin_bp.route('/subjects')
@login_required
@admin_required
def subjects():
    subjects = Subject.query.all()
    return render_template('admin/subjects.html', subjects=subjects)

@admin_bp.route('/subjects/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_subject():
    form = SubjectForm()
    if form.validate_on_submit():
        subject = Subject(name=form.name.data, description=form.description.data)
        db.session.add(subject)
        db.session.commit()
        flash('Subject added successfully!', 'success')
        return redirect(url_for('admin.subjects'))
    return render_template('admin/add_subject.html', form=form)

@admin_bp.route('/subjects/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_subject(id):
    subject = Subject.query.get_or_404(id)
    form = SubjectForm(obj=subject)
    
    if form.validate_on_submit():
        subject.name = form.name.data
        subject.description = form.description.data
        db.session.commit()
        flash('Subject updated successfully!', 'success')
        return redirect(url_for('admin.subjects'))
    
    return render_template('admin/edit_subject.html', form=form, subject=subject)

@admin_bp.route('/subjects/delete/<int:id>')
@login_required
@admin_required
def delete_subject(id):
    subject = Subject.query.get_or_404(id)
    db.session.delete(subject)
    db.session.commit()
    flash('Subject deleted successfully!', 'success')
    return redirect(url_for('admin.subjects'))

# Chapter Management
@admin_bp.route('/chapters')
@login_required
@admin_required
def chapters():
    chapters = Chapter.query.all()
    return render_template('admin/chapters.html', chapters=chapters)

@admin_bp.route('/chapters/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_chapter():
    form = ChapterForm()
    form.subject_id.choices = [(s.id, s.name) for s in Subject.query.all()]
    
    if form.validate_on_submit():
        chapter = Chapter(
            name=form.name.data,
            description=form.description.data,
            subject_id=form.subject_id.data
        )
        db.session.add(chapter)
        db.session.commit()
        flash('Chapter added successfully!', 'success')
        return redirect(url_for('admin.chapters'))
    
    return render_template('admin/add_chapter.html', form=form)

@admin_bp.route('/chapters/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_chapter(id):
    chapter = Chapter.query.get_or_404(id)
    form = ChapterForm(obj=chapter)
    form.subject_id.choices = [(s.id, s.name) for s in Subject.query.all()]
    
    if form.validate_on_submit():
        chapter.name = form.name.data
        chapter.description = form.description.data
        chapter.subject_id = form.subject_id.data
        db.session.commit()
        flash('Chapter updated successfully!', 'success')
        return redirect(url_for('admin.chapters'))
    
    return render_template('admin/edit_chapter.html', form=form, chapter=chapter)

@admin_bp.route('/chapters/delete/<int:id>')
@login_required
@admin_required
def delete_chapter(id):
    chapter = Chapter.query.get_or_404(id)
    db.session.delete(chapter)
    db.session.commit()
    flash('Chapter deleted successfully!', 'success')
    return redirect(url_for('admin.chapters'))

# Quiz Management
@admin_bp.route('/quizzes')
@login_required
@admin_required
def quizzes():
    quizzes = Quiz.query.all()
    return render_template('admin/quizzes.html', quizzes=quizzes)

@admin_bp.route('/quizzes/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_quiz():
    form = QuizForm()
    chapter_id = request.args.get('chapter_id', type=int)
    
    if chapter_id:
        chapter = Chapter.query.get_or_404(chapter_id)
    else:
        chapters = Chapter.query.all()
        if not chapters:
            flash('Please add chapters before creating a quiz.', 'warning')
            return redirect(url_for('admin.chapters'))
        chapter = chapters[0]
        chapter_id = chapter.id
    
    if form.validate_on_submit():
        quiz = Quiz(
            chapter_id=chapter_id,
            date_of_quiz=form.date_of_quiz.data,
            time_duration=form.time_duration.data,
            remarks=form.remarks.data
        )
        db.session.add(quiz)
        db.session.commit()
        flash('Quiz added successfully! Now add questions to the quiz.', 'success')
        return redirect(url_for('admin.add_question', quiz_id=quiz.id))
    
    return render_template('admin/add_quiz.html', form=form, chapter=chapter)

@admin_bp.route('/quizzes/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_quiz(id):
    quiz = Quiz.query.get_or_404(id)
    form = QuizForm(obj=quiz)
    
    if form.validate_on_submit():
        quiz.date_of_quiz = form.date_of_quiz.data
        quiz.time_duration = form.time_duration.data
        quiz.remarks = form.remarks.data
        db.session.commit()
        flash('Quiz updated successfully!', 'success')
        return redirect(url_for('admin.quizzes'))
    
    return render_template('admin/edit_quiz.html', form=form, quiz=quiz)

@admin_bp.route('/quizzes/delete/<int:id>')
@login_required
@admin_required
def delete_quiz(id):
    quiz = Quiz.query.get_or_404(id)
    db.session.delete(quiz)
    db.session.commit()
    flash('Quiz deleted successfully!', 'success')
    return redirect(url_for('admin.quizzes'))

# Question Management
@admin_bp.route('/quizzes/<int:quiz_id>/questions')
@login_required
@admin_required
def questions(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    return render_template('admin/questions.html', quiz=quiz, questions=questions)

@admin_bp.route('/quizzes/<int:quiz_id>/questions/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_question(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    form = QuestionForm()
    
    if form.validate_on_submit():
        question = Question(
            quiz_id=quiz_id,
            question_statement=form.question_statement.data,
            option1=form.option1.data,
            option2=form.option2.data,
            option3=form.option3.data,
            option4=form.option4.data,
            correct_option=form.correct_option.data
        )
        db.session.add(question)
        db.session.commit()
        flash('Question added successfully!', 'success')
        
        # Add another question or finish
        if 'add_another' in request.form:
            return redirect(url_for('admin.add_question', quiz_id=quiz_id))
        return redirect(url_for('admin.questions', quiz_id=quiz_id))
    
    return render_template('admin/add_question.html', form=form, quiz=quiz)

@admin_bp.route('/questions/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_question(id):
    question = Question.query.get_or_404(id)
    form = QuestionForm(obj=question)
    
    if form.validate_on_submit():
        question.question_statement = form.question_statement.data
        question.option1 = form.option1.data
        question.option2 = form.option2.data
        question.option3 = form.option3.data
        question.option4 = form.option4.data
        question.correct_option = form.correct_option.data
        db.session.commit()
        flash('Question updated successfully!', 'success')
        return redirect(url_for('admin.questions', quiz_id=question.quiz_id))
    
    return render_template('admin/edit_question.html', form=form, question=question)

@admin_bp.route('/questions/delete/<int:id>')
@login_required
@admin_required
def delete_question(id):
    question = Question.query.get_or_404(id)
    quiz_id = question.quiz_id
    db.session.delete(question)
    db.session.commit()
    flash('Question deleted successfully!', 'success')
    return redirect(url_for('admin.questions', quiz_id=quiz_id))

# User Management
@admin_bp.route('/users')
@login_required
@admin_required
def users():
    users = User.query.filter_by(is_admin=False).all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/delete/<int:id>')
@login_required
@admin_required
def delete_user(id):
    user = User.query.get_or_404(id)
    if user.is_admin:
        flash('Cannot delete admin user.', 'danger')
    else:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully!', 'success')
    return redirect(url_for('admin.users'))

# Search Functionality
@admin_bp.route('/search', methods=['GET', 'POST'])
@login_required
@admin_required
def search():
    form = SearchForm()
    results = []
    
    if request.method == 'POST' and form.validate_on_submit():
        query = form.query.data
        category = form.category.data
        
        if category == 'user':
            results = User.query.filter(
                (User.username.contains(query)) | 
                (User.full_name.contains(query))
            ).filter_by(is_admin=False).all()
        elif category == 'subject':
            results = Subject.query.filter(
                (Subject.name.contains(query)) | 
                (Subject.description.contains(query))
            ).all()
        elif category == 'quiz':
            results = Quiz.query.join(Chapter).filter(
                (Chapter.name.contains(query)) | 
                (Quiz.remarks.contains(query))
            ).all()
    
    return render_template('admin/search.html', form=form, results=results, category=form.category.data if form.validate_on_submit() else None)

# API Endpoints
@admin_bp.route('/api/subjects', methods=['GET'])
@login_required
@admin_required
def api_subjects():
    subjects = Subject.query.all()
    return jsonify([{
        'id': subject.id,
        'name': subject.name,
        'description': subject.description,
        'chapters_count': len(subject.chapters)
    } for subject in subjects])

@admin_bp.route('/api/chapters/<int:subject_id>', methods=['GET'])
@login_required
@admin_required
def api_chapters(subject_id):
    chapters = Chapter.query.filter_by(subject_id=subject_id).all()
    return jsonify([{
        'id': chapter.id,
        'name': chapter.name,
        'description': chapter.description,
        'quizzes_count': len(chapter.quizzes)
    } for chapter in chapters])

@admin_bp.route('/api/quiz-stats', methods=['GET'])
@login_required
@admin_required
def api_quiz_stats():
    # Get statistics for charts
    quizzes = Quiz.query.all()
    stats = []
    
    for quiz in quizzes:
        attempts = Score.query.filter_by(quiz_id=quiz.id).count()
        avg_score = db.session.query(db.func.avg(Score.percentage)).filter(Score.quiz_id == quiz.id).scalar() or 0
        
        stats.append({
            'quiz_id': quiz.id,
            'chapter_name': quiz.chapter.name,
            'subject_name': quiz.chapter.subject.name,
            'attempts': attempts,
            'avg_score': round(avg_score, 2)
        })
    
    return jsonify(stats)