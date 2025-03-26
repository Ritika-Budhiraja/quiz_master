from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DateField, TextAreaField, SelectField, DateTimeField, IntegerField, FieldList, FormField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, ValidationError

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])

class RegisterForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', 
        validators=[DataRequired(), EqualTo('password')])
    full_name = StringField('Full Name', validators=[DataRequired()])
    qualification = StringField('Qualification', validators=[DataRequired()])
    dob = DateField('Date of Birth', validators=[DataRequired()])
class SubjectForm(FlaskForm):
    name = StringField('Subject Name', validators=[DataRequired(), Length(min=2, max=120)])
    description = TextAreaField('Description', validators=[Optional()])

class ChapterForm(FlaskForm):
    subject_id = SelectField('Subject', coerce=int, validators=[DataRequired()])
    name = StringField('Chapter Name', validators=[DataRequired(), Length(min=2, max=120)])
    description = TextAreaField('Description', validators=[Optional()])

class QuestionForm(FlaskForm):
    question_text = TextAreaField('Question', validators=[DataRequired()])
    option_a = StringField('Option A', validators=[DataRequired()])
    option_b = StringField('Option B', validators=[DataRequired()])
    option_c = StringField('Option C', validators=[DataRequired()])
    option_d = StringField('Option D', validators=[DataRequired()])
    correct_option = SelectField('Correct Option', 
                               choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')],
                               validators=[DataRequired()])

class QuizForm(FlaskForm):
    chapter_id = SelectField('Chapter', coerce=int, validators=[DataRequired()])
    date_of_quiz = DateTimeField('Quiz Date', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    duration_minutes = IntegerField('Duration (minutes)', validators=[DataRequired()])
    remarks = TextAreaField('Remarks', validators=[Optional()])
    questions = FieldList(FormField(QuestionForm), min_entries=1)
