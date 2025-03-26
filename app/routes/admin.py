from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required
from app.models import Subject, Chapter, Question
from flask import Blueprint, render_template



admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
def admin_dashboard():
    return render_template('admin_dashboard.html')

@admin_bp.route('/add_subject')
@login_required
def add_subject():
    return render_template('add_subject.html')

@admin_bp.route('/add_question')
@login_required
def add_question():
    return render_template('add_question.html')
