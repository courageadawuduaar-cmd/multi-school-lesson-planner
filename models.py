from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from extensions import db

# ------------------------
# MODELS
# ------------------------

class School(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150))
    phone = db.Column(db.String(30))
    location = db.Column(db.String(150))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    users = db.relationship('User', backref='school', lazy=True)
    lessons = db.relationship('Lesson', backref='school', lazy=True)


class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)

    school_id = db.Column(db.Integer, db.ForeignKey('school.id'))

    yearly_schemes = db.relationship(
        'YearlyScheme',
        back_populates='teacher'
    )


class Lesson(db.Model):
    __tablename__ = 'lessons'

    id = db.Column(db.Integer, primary_key=True)

    # Basic info
    lesson_date = db.Column(db.Date, nullable=False)
    week_ending = db.Column(db.Date, nullable=False)
    class_name = db.Column(db.String(50), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    lesson_topic = db.Column(db.String(200), nullable=False)
    strand = db.Column(db.String(150), nullable=False)
    sub_strand = db.Column(db.String(150), nullable=False)
    day = db.Column(db.String(20), nullable=False)
    period = db.Column(db.String(50), nullable=False)
    class_size = db.Column(db.Integer, nullable=False)

    # Indicators
    performance_indicator = db.Column(db.String(200))
    content_standard_code = db.Column(db.String(50))
    indicator_code = db.Column(db.String(50))
    core_competencies = db.Column(db.String(200))
    keywords = db.Column(db.String(200))
    reference = db.Column(db.String(200))

    # Rich text
    tlr = db.Column(db.Text)
    phase1 = db.Column(db.Text)
    phase2 = db.Column(db.Text)
    phase3 = db.Column(db.Text)

    # Relations
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id'))

    # Approval workflow
    status = db.Column(db.String(20), default='submitted')  # submitted, approved, rejected
    reviewed_at = db.Column(db.DateTime)
    review_comment = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships with explicit foreign_keys
    teacher = db.relationship(
        'User',
        foreign_keys=[teacher_id],
        backref='lessons'
    )

    reviewer = db.relationship(
        'User',
        foreign_keys=[reviewed_by],
        backref='reviewed_lessons'
    )


# ------------------------
# YEARLY SCHEME
# ------------------------
class YearlyScheme(db.Model):
    __tablename__ = 'yearly_schemes'

    id = db.Column(db.Integer, primary_key=True)
    class_name = db.Column(db.String(50), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    academic_year = db.Column(db.String(20), nullable=False)
    week = db.Column(db.Integer, nullable=False)

    term1 = db.Column(db.Text, nullable=False)
    term2 = db.Column(db.Text, nullable=False)
    term3 = db.Column(db.Text, nullable=False)

    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)

    status = db.Column(db.String(20), default='pending')
    comment = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    teacher = db.relationship(
        'User',
        back_populates='yearly_schemes'
    )


# ------------------------
# TERMLY SCHEME
# ------------------------
class TermlyScheme(db.Model):
    __tablename__ = 'termly_schemes'

    id = db.Column(db.Integer, primary_key=True)
    term = db.Column(db.String(20), nullable=False)
    week = db.Column(db.String(20), nullable=False)
    strand = db.Column(db.String(150), nullable=False)
    sub_strand = db.Column(db.String(150), nullable=False)
    content_standard = db.Column(db.Text, nullable=False)
    indicator = db.Column(db.Text, nullable=False)
    resources = db.Column(db.Text)

    yearly_scheme_id = db.Column(
        db.Integer,
        db.ForeignKey('yearly_schemes.id'),
        nullable=False
    )

    status = db.Column(db.String(20), default='pending')
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    yearly_scheme = db.relationship(
        'YearlyScheme',
        backref=db.backref('termly_schemes', cascade='all, delete-orphan')
    )
