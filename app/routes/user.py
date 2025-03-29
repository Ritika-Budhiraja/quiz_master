from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Subject, Chapter, Quiz, Question, Score
from forms import QuizAttemptForm
from datetime import datetime
from wtforms import RadioField
from wtforms.validators import DataRequired

user_bp = Blueprint('user', __name__)

@user_bp.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('user.dashboard'))
    return redirect(url_for('auth.login'))

@user_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
    
    # Get recent quizzes attempted by user
    recent_scores = Score.query.filter_by(user_id=current_user.id).order_by(Score.time_stamp_of_attempt.desc()).limit(5).all()
    
    # Get all subjects for navigation
    subjects = Subject.query.all()
    
    # Get some statistics for the user
    total_quizzes_attempted = Score.query.filter_by(user_id=current_user.id).count()
    
    # Calculate average score percentage
    avg_score = db.session.query(db.func.avg(Score.percentage)).filter(Score.user_id == current_user.id).scalar() or 0
    
    # Get count of subjects and chapters explored
    explored_quizzes = db.session.query(Quiz.id).join(Score).filter(Score.user_id == current_user.id).distinct().count()
    
    return render_template('user/dashboard.html',
                           recent_scores=recent_scores,
                           subjects=subjects,
                           total_quizzes_attempted=total_quizzes_attempted,
                           avg_score=round(avg_score, 2),
                           explored_quizzes=explored_quizzes)

@user_bp.route('/subjects')
@login_required
def subjects():
    if current_user.is_admin:
        return redirect(url_for('admin.subjects'))
    
    subjects = Subject.query.all()
    return render_template('user/subjects.html', subjects=subjects)

@user_bp.route('/subjects/<int:subject_id>/chapters')
@login_required
def chapters(subject_id):
    if current_user.is_admin:
        return redirect(url_for('admin.chapters'))
    
    subject = Subject.query.get_or_404(subject_id)
    chapters = Chapter.query.filter_by(subject_id=subject_id).all()
    return render_template('user/chapters.html', subject=subject, chapters=chapters)

@user_bp.route('/chapters/<int:chapter_id>/quizzes')
@login_required
def quizzes(chapter_id):
    if current_user.is_admin:
        return redirect(url_for('admin.quizzes'))
    
    chapter = Chapter.query.get_or_404(chapter_id)
    quizzes = Quiz.query.filter_by(chapter_id=chapter_id).all()
    
    # Check which quizzes the user has already attempted
    user_scores = {score.quiz_id: score for score in Score.query.filter_by(user_id=current_user.id).all()}
    
    return render_template('user/quizzes.html', chapter=chapter, quizzes=quizzes, user_scores=user_scores)

@user_bp.route('/quizzes/<int:quiz_id>/take', methods=['GET', 'POST'])
@login_required
def take_quiz(quiz_id):
    if current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
    
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    
    if not questions:
        flash('This quiz has no questions yet.', 'warning')
        return redirect(url_for('user.quizzes', chapter_id=quiz.chapter_id))
    
    # Check if the user has already taken this quiz
    existing_score = Score.query.filter_by(user_id=current_user.id, quiz_id=quiz_id).first()
    if existing_score:
        flash('You have already taken this quiz. View your results below.', 'info')
        return redirect(url_for('user.quiz_result', score_id=existing_score.id))
    
    # Dynamically create form with questions
    class DynamicQuizForm(QuizAttemptForm):
        pass