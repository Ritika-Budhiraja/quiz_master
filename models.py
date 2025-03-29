from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    full_name = db.Column(db.String(100))
    date_of_birth = db.Column(db.Date)
    is_admin = db.Column(db.Boolean, default=False)
    
    quizzes_taken = db.relationship('QuizAttempt', backref='student', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    chapters = db.relationship('Chapter', backref='subject', lazy='dynamic')
    
class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'))
    
    quizzes = db.relationship('Quiz', backref='chapter', lazy='dynamic')
    
class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    duration_minutes = db.Column(db.Integer, default=30)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)
    
    questions = db.relationship('Question', backref='quiz', lazy='dynamic')
    attempts = db.relationship('QuizAttempt', backref='quiz', lazy='dynamic')
    
    @property
    def num_questions(self):
        return self.questions.count()

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.Text, nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'))
    
    options = db.relationship('Option', backref='question', lazy='dynamic')
    
class Option(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    option_text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))

class QuizAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'))
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    score = db.Column(db.Float, nullable=True)
    
    answers = db.relationship('UserAnswer', backref='attempt', lazy='dynamic')
    
    @property
    def is_completed(self):
        return self.end_time is not None
    
    @property
    def score_percentage(self):
        if self.score is None:
            return 0
        total_questions = self.quiz.num_questions
        if total_questions == 0:
            return 0
        return (self.score / total_questions) * 100

class UserAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey('quiz_attempt.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    selected_option_id = db.Column(db.Integer, db.ForeignKey('option.id'))
    
    question = db.relationship('Question')
    selected_option = db.relationship('Option')