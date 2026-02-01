from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_required, current_user
from models import db, User, YearlyScheme
from datetime import datetime
from forms import LoginForm  # import the form you just created
from werkzeug.security import check_password_hash
import os
from flask_wtf import FlaskForm, CSRFProtect
from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask import Flask
from models import db
from flask_wtf import CSRFProtect
from flask import Flask
from flask_login import LoginManager
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField, IntegerField, SelectField, SubmitField
from wtforms.validators import DataRequired
from flask_wtf.csrf import CSRFProtect
from utils.pdf_generator import lesson_to_pdf
from flask import send_file
from sqlalchemy import func
from datetime import timedelta
from models import db, User, Lesson, School
from werkzeug.security import generate_password_hash
import tempfile
from forms import ForgotPasswordForm, ResetPasswordForm
from forms import LoginForm, ForgotPasswordForm, ResetPasswordForm
from flask import abort




# Import models
from models import db, User, YearlyScheme, Lesson
from forms import LessonForm


# ------------------------
# APP SETUP
# ------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")
csrf = CSRFProtect(app)

# ------------------------
# DATABASE CONFIG
# ------------------------
basedir = os.path.abspath(os.path.dirname(__file__))

DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    # Render / Production (PostgreSQL)
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL.replace(
        "postgres://", "postgresql://"
    )
else:
    # Local development (SQLite)
    db_path = os.path.join(basedir, "instance", "database.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


# Import db from models
from models import db
db.init_app(app)

with app.app_context():
    db.create_all()
    create_super_admin()


# Login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Import models after db.init_app
from models import User, School, Lesson, YearlyScheme, TermlyScheme

# ------------------------
# LOGIN LOADER
# ------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ------------------------
# SUPER ADMIN CREATION (first run)
# ------------------------
def create_super_admin():
    admin = User.query.filter_by(email='admin@example.com').first()
    if not admin:
        admin = User(
            name='Super Admin',
            email='admin@example.com',
            password=generate_password_hash('admin123'),
            role='super_admin'
        )
        db.session.add(admin)
        db.session.commit()
        print("Super admin created! Email: admin@example.com | Password: admin123")

# Teachers' lessons submitted to this headmaster
@app.route('/headmaster/teachers-lessons')
@login_required
def teachers_lessons():
    if current_user.role != 'headmaster':
        flash("Unauthorized access!", "danger")
        return redirect(url_for("home"))

    lessons = (
        Lesson.query
        .join(Lesson.teacher)   # explicit join via teacher_id
        .filter(User.school_id == current_user.school_id)
        .all()
    )

    return render_template('teachers_lessons.html', lessons=lessons)


# Super Admin: Create School
@app.route('/super-admin/create-school', methods=['GET', 'POST'])
@login_required
def create_school():
    if current_user.role != 'super_admin':
        flash("Unauthorized access!", "danger")
        return redirect(url_for('home'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        location = request.form.get('location')

        if not name:
            flash("School name is required.", "warning")
            return redirect(url_for('create_school'))

        # Create and save the new school
        school = School(name=name, email=email, phone=phone, location=location)
        db.session.add(school)
        db.session.commit()
        flash(f"School '{name}' created successfully!", "success")
        return redirect(url_for('super_admin_dashboard'))

    # If GET request, render the create school form
    return render_template('create_school.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'teacher':
            return redirect(url_for('teacher_dashboard'))
        elif current_user.role == 'headmaster':
            return redirect(url_for('headmaster_dashboard'))
        elif current_user.role == 'super_admin':
            return redirect(url_for('super_admin_dashboard'))
        else:
            return redirect(url_for('home'))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            flash("Logged in successfully!", "success")

            if user.role == 'teacher':
                return redirect(url_for('teacher_dashboard'))
            elif user.role == 'headmaster':
                return redirect(url_for('headmaster_dashboard'))
            elif user.role == 'super_admin':
                return redirect(url_for('super_admin_dashboard'))
            else:
                return redirect(url_for('home'))

        flash("Invalid email or password", "danger")

    return render_template("login.html", form=form)


@app.route('/super-admin/edit-school/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_school(id):
    if current_user.role != 'super_admin':
        flash("Unauthorized access!", "danger")
        return redirect(url_for('home'))

    school = School.query.get_or_404(id)

    if request.method == 'POST':
        school.name = request.form.get('name')
        school.email = request.form.get('email')
        school.phone = request.form.get('phone')
        school.location = request.form.get('location')
        
        db.session.commit()
        flash(f"School '{school.name}' updated successfully!", "success")
        return redirect(url_for('super_admin_dashboard'))

    return render_template('edit_school.html', school=school)

@app.route('/super-admin/delete-school/<int:school_id>', methods=['POST'])
@login_required
def delete_school(school_id):
    if current_user.role != 'super_admin':
        flash("Unauthorized access!", "danger")
        return redirect(url_for('home'))

    school = School.query.get_or_404(school_id)
    db.session.delete(school)
    db.session.commit()
    flash(f"School '{school.name}' deleted!", "info")
    return redirect(url_for('list_schools'))

@app.route('/super-admin/headmasters')
@login_required
def list_headmasters():
    if current_user.role != 'super_admin':
        flash("Unauthorized access!", "danger")
        return redirect(url_for('home'))

    # Fetch all headmasters
    headmasters = User.query.filter_by(role='headmaster').all()
    return render_template('list_headmasters.html', headmasters=headmasters)

@app.route('/super-admin/edit-headmaster/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_headmaster(id):
    if current_user.role != 'super_admin':
        flash("Unauthorized access!", "danger")
        return redirect(url_for('home'))

    headmaster = User.query.get_or_404(id)

    if request.method == 'POST':
        headmaster.name = request.form.get('name')
        headmaster.email = request.form.get('email')
        headmaster.school_id = request.form.get('school_id')
        db.session.commit()
        flash(f"Headmaster '{headmaster.name}' updated successfully!", "success")
        return redirect(url_for('list_headmasters'))

    # Fetch all schools for assignment
    schools = School.query.all()
    return render_template('edit_headmaster.html', headmaster=headmaster, schools=schools)

@app.route('/super-admin/delete-headmaster/<int:headmaster_id>', methods=['POST'])
@login_required
def delete_headmaster(headmaster_id):
    if current_user.role != 'super_admin':
        flash("Unauthorized access!", "danger")
        return redirect(url_for('home'))

    headmaster = User.query.get_or_404(headmaster_id)
    db.session.delete(headmaster)
    db.session.commit()
    flash(f"Headmaster '{headmaster.name}' deleted successfully!", "success")
    return redirect(url_for('list_headmasters'))


# Super Admin: Create Headmaster
@app.route('/super-admin/create-headmaster', methods=['GET', 'POST'])
@login_required
def create_headmaster():
    if current_user.role != 'super_admin':
        flash("Unauthorized access!", "danger")
        return redirect(url_for('home'))

    schools = School.query.all()

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        school_id = request.form.get('school_id')

        if not all([name, email, password, school_id]):
            flash("All fields are required.", "warning")
            return redirect(url_for('create_headmaster'))

        # Create user
        headmaster = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            role='headmaster',
            school_id=int(school_id)
        )
        db.session.add(headmaster)
        db.session.commit()
        flash(f"Headmaster '{name}' created successfully!", "success")
        return redirect(url_for('super_admin_dashboard'))

    return render_template('create_headmaster.html', schools=schools)


# Super Admin: List all schools
@app.route('/super-admin/schools')
@login_required
def list_schools():
    if current_user.role != 'super_admin':
        flash("Unauthorized access!", "danger")
        return redirect(url_for('home'))

    schools = School.query.all()
    return render_template('list_schools.html', schools=schools)




@app.context_processor
def inject_now():
    from datetime import datetime
    return {'current_year': datetime.utcnow().year}

# ------------------------
# ROUTES
# ------------------------
@app.route('/')
def home():
    return render_template("home.html", datetime=datetime)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))


# ------------------------
# DASHBOARDS
# ------------------------
@app.route('/super-admin')
@login_required
def super_admin_dashboard():
    if current_user.role != 'super_admin':
        flash("Unauthorized access!", "danger")
        return redirect(url_for("home"))
    schools = School.query.all()
    return render_template("super_admin_dashboard.html", schools=schools)

# ------------------------
# HEADMASTER DASHBOARD
# ------------------------
@app.route('/headmaster')
@login_required
def headmaster_dashboard():
    if current_user.role != 'headmaster':
        flash("Unauthorized access", "danger")
        return redirect(url_for('home'))

    # Teachers in this headmaster's school
    teachers = User.query.filter_by(
        role='teacher',
        school_id=current_user.school_id
    ).all()

    total_teachers = len(teachers)

    # Yearly schemes for this school
    yearly_schemes = YearlyScheme.query.filter_by(
        school_id=current_user.school_id
    ).order_by(YearlyScheme.created_at.desc()).all()

    total_schemes = len(yearly_schemes)

    # Lesson statistics (adjust model/field names if needed)
    total_lessons = Lesson.query.filter_by(
        school_id=current_user.school_id
    ).count()

    pending_lessons = Lesson.query.filter_by(
        school_id=current_user.school_id,
        status='pending'
    ).count()

    approved_lessons = Lesson.query.filter_by(
        school_id=current_user.school_id,
        status='approved'
    ).count()

    return render_template(
        'headmaster_dashboard.html',
        teachers=teachers,
        yearly_schemes=yearly_schemes,
        total_teachers=total_teachers,
        total_schemes=total_schemes,
        total_lessons=total_lessons,
        pending_lessons=pending_lessons,
        approved_lessons=approved_lessons
    )

@app.route("/lesson/<int:lesson_id>/approve", methods=["POST"])
@login_required
def approve_lesson(lesson_id):
    if current_user.role != "headmaster":
        flash("Unauthorized", "danger")
        return redirect(url_for("index"))

    lesson = Lesson.query.get_or_404(lesson_id)

    # SECURITY: ensure same school
    if lesson.school_id != current_user.school_id:
        flash("Unauthorized access", "danger")
        return redirect(url_for("lesson_approvals"))

    comment = request.form.get("comment")

    lesson.status = "approved"
    lesson.review_comment = comment
    lesson.reviewed_by = current_user.id
    lesson.reviewed_at = datetime.utcnow()

    db.session.commit()
    flash("Lesson approved with comment.", "success")
    return redirect(url_for("lesson_approvals"))

@app.route("/lesson/<int:lesson_id>/reject", methods=["POST"])
@login_required
def reject_lesson(lesson_id):
    if current_user.role != "headmaster":
        flash("Unauthorized", "danger")
        return redirect(url_for("index"))

    lesson = Lesson.query.get_or_404(lesson_id)

    if lesson.school_id != current_user.school_id:
        flash("Unauthorized access", "danger")
        return redirect(url_for("lesson_approvals"))

    comment = request.form.get("comment")

    if not comment:
        flash("Rejection comment is required.", "danger")
        return redirect(url_for("lesson_approvals"))

    lesson.status = "rejected"
    lesson.review_comment = comment
    lesson.reviewed_by = current_user.id
    lesson.reviewed_at = datetime.utcnow()

    db.session.commit()
    flash("Lesson rejected with comment.", "warning")
    return redirect(url_for("lesson_approvals"))

@app.route("/lesson/<int:lesson_id>/edit", methods=["GET", "POST"])
@login_required
def edit_lesson(lesson_id):

    lesson = Lesson.query.get_or_404(lesson_id)

    # 🔐 Security checks
    if current_user.role != "teacher":
        abort(403)

    if lesson.teacher_id != current_user.id:
        abort(403)

    if lesson.status != "rejected":
        flash("Only rejected lessons can be edited.", "warning")
        return redirect(url_for("view_lessons"))

    form = LessonForm(obj=lesson)  # reuse your existing lesson form

    if form.validate_on_submit():

        # 🔄 Update lesson fields
        form.populate_obj(lesson)

        # 🔁 Reset approval workflow
        lesson.status = "submitted"
        lesson.review_comment = None
        lesson.reviewed_by = None
        lesson.reviewed_at = None
        lesson.created_at = datetime.utcnow()

        db.session.commit()

        flash("Lesson updated and resubmitted for approval.", "success")
        return redirect(url_for("view_lessons"))

    return render_template(
        "edit_lesson.html",   # 🔁 change if your template name differs
        form=form,
        lesson=lesson
    )

@app.route("/headmaster/lesson-approvals")
@login_required
def lesson_approvals():
    if current_user.role != "headmaster":
        flash("Access denied.", "danger")
        return redirect(url_for("home"))

    lessons = (
        Lesson.query
        .filter(Lesson.school_id == current_user.school_id)
        .order_by(Lesson.created_at.desc())
        .all()
    )

    return render_template("lesson_approvals.html", lessons=lessons)


# ------------------------
# CREATE TEACHER
# ------------------------
@app.route('/headmaster/create-teacher', methods=['GET', 'POST'])
@login_required
def create_teacher():
    if current_user.role != 'headmaster':
        flash('Access denied', 'danger')
        return redirect(url_for('home'))

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        teacher = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            role='teacher',
            school_id=current_user.school_id
        )
        db.session.add(teacher)
        db.session.commit()
        flash('Teacher created successfully!', 'success')
        return redirect(url_for('list_teachers'))

    return render_template('create_teacher.html')

# LIST ALL TEACHERS
# -----------------------------
@app.route('/headmaster/list-teachers')
@login_required
def list_teachers():
    if current_user.role != 'headmaster':
        flash('Access denied', 'danger')
        return redirect(url_for('home'))

    teachers = User.query.filter_by(
        role='teacher',
        school_id=current_user.school_id
    ).all()

    return render_template('list_teachers.html', teachers=teachers)

# ------------------------
# EDIT TEACHER
# ------------------------
@app.route('/headmaster/edit-teacher/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_teacher(id):
    if current_user.role != 'headmaster':
        flash("Unauthorized access!", "danger")
        return redirect(url_for("home"))

    teacher = User.query.get_or_404(id)
    if teacher.school_id != current_user.school_id:
        flash("Cannot edit teacher from another school!", "danger")
        return redirect(url_for('headmaster_dashboard'))

    if request.method == 'POST':
        teacher.name = request.form.get('name')
        teacher.email = request.form.get('email')
        teacher.password = generate_password_hash(request.form.get('password')) if request.form.get('password') else teacher.password
        db.session.commit()
        flash(f"Teacher '{teacher.name}' updated successfully!", "success")
        return redirect(url_for('headmaster_dashboard'))

    return render_template('edit_teacher.html', teacher=teacher)

# ------------------------
# DELETE TEACHER
# ------------------------
@app.route('/headmaster/delete-teacher/<int:id>', methods=['POST'])
@login_required
def delete_teacher(id):
    if current_user.role != 'headmaster':
        flash("Unauthorized access!", "danger")
        return redirect(url_for("home"))

    teacher = User.query.get_or_404(id)
    if teacher.school_id != current_user.school_id:
        flash("Cannot delete teacher from another school!", "danger")
        return redirect(url_for('headmaster_dashboard'))

    db.session.delete(teacher)
    db.session.commit()
    flash(f"Teacher '{teacher.name}' deleted successfully!", "success")
    return redirect(url_for('headmaster_dashboard'))

@app.route('/headmaster/schemes')
@login_required
def headmaster_schemes():
    if current_user.role != 'headmaster':
        flash("Unauthorized access", "danger")
        return redirect(url_for('home'))

    schemes = YearlyScheme.query.filter_by(
        school_id=current_user.school_id
    ).order_by(YearlyScheme.created_at.desc()).all()

    return render_template(
        'headmaster_schemes.html',
        schemes=schemes
    )

@app.route('/headmaster/approve-scheme/<int:scheme_id>')
@login_required
def approve_scheme(scheme_id):
    scheme = YearlyScheme.query.get_or_404(scheme_id)
    if scheme.school_id != current_user.school_id:
        flash("Access denied", "danger")
        return redirect(url_for("review_yearly_schemes"))
    scheme.status = 'approved'
    db.session.commit()
    flash("Scheme approved.", "success")
    return redirect(url_for('review_yearly_schemes'))


@app.route('/headmaster/reject-scheme/<int:scheme_id>')
@login_required
def reject_scheme(scheme_id):
    scheme = YearlyScheme.query.get_or_404(scheme_id)
    if scheme.school_id != current_user.school_id:
        flash("Access denied", "danger")
        return redirect(url_for("review_yearly_schemes"))
    scheme.status = 'rejected'
    db.session.commit()
    flash("Scheme rejected.", "success")
    return redirect(url_for('review_yearly_schemes'))

# ------------------------
# APPROVE / REJECT TEACHER (optional workflow)
# ------------------------
@app.route('/headmaster/approve-teacher/<int:id>', methods=['POST'])
@login_required
def approve_teacher(id):
    if current_user.role != 'headmaster':
        flash("Unauthorized access!", "danger")
        return redirect(url_for("home"))

    teacher = User.query.get_or_404(id)
    if teacher.school_id != current_user.school_id:
        flash("Cannot approve teacher from another school!", "danger")
        return redirect(url_for('headmaster_dashboard'))

    teacher.status = 'approved'
    db.session.commit()
    flash(f"Teacher '{teacher.name}' approved!", "success")
    return redirect(url_for('headmaster_dashboard'))

@app.route('/headmaster/reject-teacher/<int:id>', methods=['POST'])
@login_required
def reject_teacher(id):
    if current_user.role != 'headmaster':
        flash("Unauthorized access!", "danger")
        return redirect(url_for("home"))

    teacher = User.query.get_or_404(id)
    if teacher.school_id != current_user.school_id:
        flash("Cannot reject teacher from another school!", "danger")
        return redirect(url_for('headmaster_dashboard'))

    teacher.status = 'rejected'
    db.session.commit()
    flash(f"Teacher '{teacher.name}' rejected!", "info")
    return redirect(url_for('headmaster_dashboard'))

@app.route('/teacher/dashboard')
@login_required
def teacher_dashboard():
    if current_user.role != 'teacher':
        flash("Unauthorized access", "danger")
        return redirect(url_for('home'))

    # ================= YEARLY SCHEMES =================
    approved_schemes = YearlyScheme.query.filter_by(
        teacher_id=current_user.id,
        status='approved'
    ).all()

    # ================= LESSON STATS =================
    total_lessons = Lesson.query.filter_by(
        teacher_id=current_user.id
    ).count()

    approved_lessons = Lesson.query.filter_by(
        teacher_id=current_user.id,
        status='approved'
    ).count()

    pending_lessons = Lesson.query.filter_by(
        teacher_id=current_user.id,
        status='pending'
    ).count()

    return render_template(
        'teacher_dashboard.html',
        approved_schemes=approved_schemes,
        total_lessons=total_lessons,
        approved_lessons=approved_lessons,
        pending_lessons=pending_lessons
    )

@app.route('/teacher/submit-scheme', methods=['GET', 'POST'])
@login_required
def submit_scheme():
    if current_user.role != 'teacher':
        flash("Unauthorized access!", "danger")
        return redirect(url_for('home'))

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')

        if not title:
            flash("Scheme title is required.", "warning")
            return redirect(url_for('submit_scheme'))

        scheme = SchemeOfLearning(
            title=title,
            description=description,
            teacher_id=current_user.id,
            status='Pending'  # automatically pending for headmaster approval
        )
        db.session.add(scheme)
        db.session.commit()
        flash("Scheme submitted successfully!", "success")
        return redirect(url_for('teacher_dashboard'))

    return render_template('submit_scheme.html')

@app.route('/teacher/my-schemes')
@login_required
def my_schemes():
    if current_user.role != 'teacher':
        flash("Unauthorized access!", "danger")
        return redirect(url_for('home'))

    schemes = SchemeOfLearning.query.filter_by(teacher_id=current_user.id).all()
    return render_template('my_schemes.html', schemes=schemes)


@app.route('/headmaster/yearly-schemes')
@login_required
def vet_yearly_schemes():
    if current_user.role != 'headmaster':
        flash("Unauthorized access", "danger")
        return redirect(url_for('home'))

    schemes = YearlyScheme.query.filter_by(
        school_id=current_user.school_id
    ).order_by(YearlyScheme.created_at.desc()).all()

    return render_template('vet_yearly_schemes.html', schemes=schemes)

@app.route('/headmaster/schemes/<int:scheme_id>', methods=['GET', 'POST'])
@login_required
def view_yearly_scheme(scheme_id):
    if current_user.role != 'headmaster':
        flash("Unauthorized access", "danger")
        return redirect(url_for('home'))

    scheme = YearlyScheme.query.get_or_404(scheme_id)

    if scheme.school_id != current_user.school_id:
        flash("Access denied", "danger")
        return redirect(url_for('headmaster_dashboard'))

    if request.method == 'POST':
        scheme.status = request.form['status']
        scheme.comment = request.form.get('comment')
        db.session.commit()
        flash("Scheme reviewed successfully", "success")
        return redirect(url_for('headmaster_schemes'))

    return render_template('review_yearly_scheme.html', scheme=scheme)

@app.route('/headmaster/termly-schemes')
@login_required
def vet_termly_schemes():
    if current_user.role != 'headmaster':
        flash("Unauthorized access", "danger")
        return redirect(url_for('home'))

    schemes = TermlyScheme.query.join(YearlyScheme).filter(
        YearlyScheme.school_id == current_user.school_id
    ).order_by(TermlyScheme.created_at.desc()).all()

    return render_template('vet_termly_schemes.html', schemes=schemes)

# REVIEW SUBMITTED YEARLY SCHEMES
# -----------------------------
@app.route('/headmaster/review-yearly-schemes')
@login_required
def review_yearly_schemes():
    if current_user.role != 'headmaster':
        flash('Access denied', 'danger')
        return redirect(url_for('home'))

    # Fetch all teacher-submitted schemes for this school
    schemes = YearlyScheme.query.filter_by(
        school_id=current_user.school_id
    ).order_by(YearlyScheme.created_at.desc()).all()

    return render_template('review_yearly_scheme.html', schemes=schemes)

@app.route('/teacher/yearly-scheme/submit', methods=['GET', 'POST'])
@login_required
def submit_yearly_scheme():
    if current_user.role != 'teacher':
        flash("Unauthorized access", "danger")
        return redirect(url_for('home'))

    if request.method == 'POST':
        class_name = request.form.get('class_name')
        subject = request.form.get('subject')
        academic_year = request.form.get('academic_year')
        week = request.form.get('week')
        term1 = request.form.get('term1')
        term2 = request.form.get('term2')
        term3 = request.form.get('term3')

        scheme = YearlyScheme(
            class_name=class_name,
            subject=subject,
            academic_year=academic_year,
            week=week,
            term1=term1,
            term2=term2,
            term3=term3,
            teacher_id=current_user.id,
            school_id=current_user.school_id
        )
        db.session.add(scheme)
        db.session.commit()
        flash("Yearly Scheme submitted successfully!", "success")
        return redirect(url_for('teacher_dashboard'))

    return render_template('submit_yearly_scheme.html')

@app.route('/teacher/submit-termly-scheme/<int:yearly_scheme_id>', methods=['GET', 'POST'])
@login_required
def submit_termly_scheme(yearly_scheme_id):
    if current_user.role != 'teacher':
        flash("Unauthorized access!", "danger")
        return redirect(url_for('home'))

    yearly_scheme = YearlyScheme.query.get_or_404(yearly_scheme_id)

    if request.method == 'POST':
        termly = TermlyScheme(
            yearly_scheme_id=yearly_scheme.id,
            term=request.form.get('week'),
            scheme_content=f"Strand: {request.form['strand']}\n"
                           f"Sub-Strand: {request.form['sub_strand']}\n"
                           f"Content Standard: {request.form['content_standard']}\n"
                           f"Indicator: {request.form['indicator']}\n"
                           f"Resources: {request.form['resources']}"
        )
        db.session.add(termly)
        db.session.commit()
        flash("Termly Scheme submitted successfully!", "success")
        return redirect(url_for('teacher_dashboard'))

    return render_template('submit_termly_scheme.html', yearly_scheme_id=yearly_scheme_id)

@app.route('/teacher/lessons/create', methods=['GET', 'POST'])
@login_required
def create_lesson():
    if current_user.role != 'teacher':
        flash("Unauthorized access", "danger")
        return redirect(url_for('home'))

    form = LessonForm()

    if form.validate_on_submit():
        lesson = Lesson(
            lesson_date=form.lesson_date.data,
            week_ending=form.week_ending.data,
            class_name=form.class_name.data,
            subject=form.subject.data,
            lesson_topic=form.lesson_title.data,       # ✅ updated to match form
            strand=form.strand.data,
            sub_strand=form.sub_strand.data,
            day=form.day.data,
            period=form.period.data,
            class_size=form.class_size.data,
            performance_indicator=form.performance_indicator.data,
            content_standard_code=form.content_standard_code.data,
            indicator_code=form.indicator_code.data,
            core_competencies=form.core_competencies.data,
            keywords=form.keywords.data,
            reference=form.reference.data,
            tlr=form.tlr.data,
            phase1=form.phase1_starter.data,           
            phase2=form.phase2_main.data,              
            phase3=form.phase3_reflection.data,        
            teacher_id=current_user.id,
            school_id=current_user.school_id,
            status='pending'  # ✅ important: set default status
        )
        db.session.add(lesson)
        db.session.commit()
        flash("Lesson created successfully!", "success")
        return redirect(url_for('view_lessons'))

    return render_template('create_lesson.html', form=form)

@app.route('/lessons/<int:lesson_id>')
@login_required
def view_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)

    # 🔐 ROLE-BASED ACCESS CONTROL
    if current_user.role == 'teacher':
        # Teachers can only view their own lessons
        if lesson.teacher_id != current_user.id:
            flash("Unauthorized access", "danger")
            return redirect(url_for('home'))

    elif current_user.role == 'headmaster':
        # Headmasters can only view lessons in their school
        if lesson.school_id != current_user.school_id:
            flash("Unauthorized access", "danger")
            return redirect(url_for('lesson_approvals'))

    else:
        flash("Unauthorized access", "danger")
        return redirect(url_for('home'))

    return render_template('view_lesson.html', lesson=lesson)

@app.route('/teacher/lessons')
@login_required
def view_lessons():
    if current_user.role != 'teacher':
        flash("Unauthorized access", "danger")
        return redirect(url_for('home'))

    lessons = (
        Lesson.query
        .filter_by(teacher_id=current_user.id)
        .order_by(Lesson.created_at.desc())
        .all()
    )
    return render_template('view_lessons.html', lessons=lessons)

# ------------------------
# FORGOT PASSWORD
# ------------------------
@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    form = ForgotPasswordForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            session["reset_user_id"] = user.id
            return redirect(url_for("reset_password"))
        else:
            flash("Email not found.", "danger")

    return render_template("forgot_password.html", form=form)

@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    if "reset_user_id" not in session:
        flash("Password reset session expired.", "danger")
        return redirect(url_for("forgot_password"))

    form = ResetPasswordForm()
    user = User.query.get(session["reset_user_id"])

    if form.validate_on_submit():
        user.password = generate_password_hash(form.password.data)
        db.session.commit()
        session.pop("reset_user_id", None)

        flash("Password reset successful. You can now log in.", "success")
        return redirect(url_for("login"))

    return render_template("reset_password.html", form=form)



@app.route("/lesson/<int:lesson_id>/download")
@login_required
def download_lesson_pdf(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)

    # Teachers can only download their own lessons
    if current_user.role == "teacher" and lesson.teacher_id != current_user.id:
        flash("Access denied.", "danger")
        return redirect(url_for("dashboard"))

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    lesson_to_pdf(lesson, temp_file.name)

    return send_file(
        temp_file.name,
        as_attachment=True,
        download_name=f"lesson_{lesson.id}.pdf"
    )

@app.route("/headmaster/weekly-summary")
@login_required
def weekly_summary():
    if current_user.role != "headmaster":
        flash("Access denied.", "danger")
        return redirect(url_for("index"))

    today = datetime.utcnow().date()
    start_week = today - timedelta(days=today.weekday())
    end_week = start_week + timedelta(days=6)

    summary = (
        db.session.query(
            Lesson.status,
            func.count(Lesson.id)
        )
        .filter(Lesson.lesson_date.between(start_week, end_week))
        .group_by(Lesson.status)
        .all()
    )

    stats = {status: count for status, count in summary}

    return render_template(
        "weekly_summary.html",
        start_week=start_week,
        end_week=end_week,
        stats=stats
    )

# ------------------------
# RUN APP
# ------------------------
if __name__ == "__main__":
    # Ensure instance folder exists
    os.makedirs(os.path.join(basedir, "instance"), exist_ok=True)

    with app.app_context():
        db.create_all()
        create_super_admin()

    app.run(debug=True)

    # Run app so it is accessible to other computers on the network
    app.run(host="0.0.0.0", port=5000, debug=True)