from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DateField, SelectField, TextAreaField, SubmitField
from wtforms import StringField, IntegerField, SelectField, TextAreaField, DateField, SubmitField
from wtforms.validators import DataRequired, Optional
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")
    submit = SubmitField("Login")

class LessonForm(FlaskForm):
    lesson_date = DateField('Lesson Date', validators=[DataRequired()])
    week_ending = DateField('Week Ending', validators=[DataRequired()])
    class_name = SelectField(
        'Class',
        choices=[('P1','Primary 1'), ('P2','Primary 2'), ('P3','Primary 3'),
                 ('P4','Primary 4'), ('P5','Primary 5'), ('P6','Primary 6')],
        validators=[DataRequired()]
    )
    subject = StringField('Subject', validators=[DataRequired()])
    lesson_title = StringField('Lesson', validators=[DataRequired()])
    strand = StringField('Strand', validators=[DataRequired()])
    sub_strand = StringField('Sub-strand', validators=[DataRequired()])
    day = SelectField(
        'Day',
        choices=[('Monday','Monday'), ('Tuesday','Tuesday'), ('Wednesday','Wednesday'),
                 ('Thursday','Thursday'), ('Friday','Friday')],
        validators=[DataRequired()]
    )
    period = StringField('Period', validators=[DataRequired()])
    class_size = IntegerField('Class Size', validators=[DataRequired()])
    performance_indicator = TextAreaField('Performance Indicator', validators=[DataRequired()])
    content_standard_code = StringField('Content Standard Code', validators=[DataRequired()])
    indicator_code = StringField('Indicator Code', validators=[DataRequired()])
    core_competencies = TextAreaField('Core Competencies', validators=[DataRequired()])
    keywords = StringField('Keywords', validators=[Optional()])
    tlr = TextAreaField('Teaching & Learning Resources (TLR)', validators=[DataRequired()])
    reference = TextAreaField('Reference', validators=[Optional()])
    phase1_starter = TextAreaField('Phase 1 (Starter)', validators=[DataRequired()])
    phase2_main = TextAreaField('Phase 2 (Main)', validators=[DataRequired()])
    phase3_reflection = TextAreaField('Phase 3 (Reflections)', validators=[DataRequired()])
    
    submit = SubmitField('Create Lesson')


class ForgotPasswordForm(FlaskForm):
    email = StringField(
        "Email",
        validators=[DataRequired(), Email()]
    )
    submit = SubmitField("Continue")


class ResetPasswordForm(FlaskForm):
    password = PasswordField(
        "New Password",
        validators=[DataRequired(), Length(min=6)]
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Reset Password")