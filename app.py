from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from datetime import datetime, timedelta, timezone
import csv
import io
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///studysphere.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    study_sessions = db.relationship('StudySession', backref='user', lazy=True, cascade='all, delete-orphan')
    goals = db.relationship('Goal', backref='user', lazy=True, cascade='all, delete-orphan')
    notes = db.relationship('Note', backref='user', lazy=True, cascade='all, delete-orphan')

class StudySession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    duration_hours = db.Column(db.Integer, default=0)
    duration_minutes = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text, nullable=True)
    date = db.Column(db.Date, nullable=False, default=lambda: datetime.now(timezone.utc).date())
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    target_hours = db.Column(db.Integer, default=0)
    current_hours = db.Column(db.Integer, default=0)
    goal_type = db.Column(db.String(20), default='daily')  # daily, weekly
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    due_date = db.Column(db.Date, nullable=True)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    subject = db.Column(db.String(100), nullable=True)
    important = db.Column(db.Boolean, default=False)
    revision_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'danger')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return render_template('register.html')
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        
        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Login unsuccessful. Please check username and password.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get study statistics
    total_sessions = StudySession.query.filter_by(user_id=current_user.id).count()
    total_hours = sum(s.duration_hours + s.duration_minutes/60 for s in current_user.study_sessions)
    
    # Weekly analytics
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    weekly_sessions = StudySession.query.filter(
        StudySession.user_id == current_user.id,
        StudySession.date >= week_ago.date()
    ).all()
    weekly_hours = sum(s.duration_hours + s.duration_minutes/60 for s in weekly_sessions)
    
    # Subject breakdown
    subject_stats = {}
    for session in current_user.study_sessions:
        if session.subject not in subject_stats:
            subject_stats[session.subject] = 0
        subject_stats[session.subject] += session.duration_hours + session.duration_minutes/60
    
    # Goals progress
    active_goals = Goal.query.filter_by(user_id=current_user.id, completed=False).all()
    goals_progress = []
    for goal in active_goals:
        progress = min(100, (goal.current_hours / goal.target_hours * 100)) if goal.target_hours > 0 else 0
        goals_progress.append({
            'title': goal.title,
            'progress': progress,
            'current': goal.current_hours,
            'target': goal.target_hours
        })
    
    # Recent sessions
    recent_sessions = StudySession.query.filter_by(user_id=current_user.id).order_by(StudySession.date.desc()).limit(5).all()
    
    # Calculate streak
    study_dates = sorted(set(s.date for s in current_user.study_sessions), reverse=True)
    streak = 0
    if study_dates:
        current_date = datetime.now(timezone.utc).date()
        if study_dates[0] == current_date or study_dates[0] == current_date - timedelta(days=1):
            streak = 1
            for i in range(1, len(study_dates)):
                if study_dates[i] == study_dates[i-1] - timedelta(days=1):
                    streak += 1
                else:
                    break
    
    return render_template('dashboard.html', 
                         total_sessions=total_sessions,
                         total_hours=round(total_hours, 1),
                         weekly_hours=round(weekly_hours, 1),
                         subject_stats=subject_stats,
                         goals_progress=goals_progress,
                         recent_sessions=recent_sessions,
                         streak=streak)

@app.route('/sessions', methods=['GET', 'POST'])
@login_required
def sessions():
    if request.method == 'POST':
        subject = request.form.get('subject')
        duration_hours = int(request.form.get('duration_hours', 0))
        duration_minutes = int(request.form.get('duration_minutes', 0))
        notes = request.form.get('notes')
        date_str = request.form.get('date')
        
        if date_str:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            date = datetime.now(timezone.utc).date()
        
        session = StudySession(
            user_id=current_user.id,
            subject=subject,
            duration_hours=duration_hours,
            duration_minutes=duration_minutes,
            notes=notes,
            date=date
        )
        db.session.add(session)
        
        # Update goals
        if date:
            active_goals = Goal.query.filter_by(user_id=current_user.id, completed=False).all()
            for goal in active_goals:
                if goal.goal_type == 'daily' and goal.due_date == date:
                    goal.current_hours += duration_hours + duration_minutes/60
                    if goal.current_hours >= goal.target_hours:
                        goal.completed = True
                elif goal.goal_type == 'weekly':
                    goal.current_hours += duration_hours + duration_minutes/60
                    if goal.current_hours >= goal.target_hours:
                        goal.completed = True
        
        db.session.commit()
        flash('Study session added successfully!', 'success')
        return redirect(url_for('sessions'))
    
    all_sessions = StudySession.query.filter_by(user_id=current_user.id).order_by(StudySession.date.desc()).all()
    subjects = ['Mathematics', 'Programming', 'Science', 'AI & Machine Learning', 
                'Data Structures', 'Web Development', 'Aptitude', 'Other']
    current_date = datetime.now(timezone.utc).date().strftime('%Y-%m-%d')
    
    return render_template('sessions.html', sessions=all_sessions, subjects=subjects, current_date=current_date)

@app.route('/sessions/<int:session_id>/delete', methods=['POST'])
@login_required
def delete_session(session_id):
    session = StudySession.query.get_or_404(session_id)
    if session.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('sessions'))
    
    db.session.delete(session)
    db.session.commit()
    flash('Study session deleted.', 'success')
    return redirect(url_for('sessions'))

@app.route('/analytics')
@login_required
def analytics():
    # Get all sessions for charts
    sessions = StudySession.query.filter_by(user_id=current_user.id).order_by(StudySession.date.asc()).all()
    
    # Weekly data for last 8 weeks
    weekly_data = {}
    for session in sessions:
        week_start = session.date - timedelta(days=session.date.weekday())
        week_key = week_start.strftime('%Y-%m-%d')
        if week_key not in weekly_data:
            weekly_data[week_key] = 0
        weekly_data[week_key] += session.duration_hours + session.duration_minutes/60
    
    # Subject distribution
    subject_data = {}
    for session in sessions:
        if session.subject not in subject_data:
            subject_data[session.subject] = 0
        subject_data[session.subject] += session.duration_hours + session.duration_minutes/60
    
    # Monthly data
    monthly_data = {}
    for session in sessions:
        month_key = session.date.strftime('%Y-%m')
        if month_key not in monthly_data:
            monthly_data[month_key] = 0
        monthly_data[month_key] += session.duration_hours + session.duration_minutes/60
    
    # Daily productivity (last 30 days)
    daily_data = {}
    for i in range(30):
        date = datetime.now(timezone.utc) - timedelta(days=i)
        date_key = date.strftime('%Y-%m-%d')
        daily_data[date_key] = 0
    
    for session in sessions:
        date_key = session.date.strftime('%Y-%m-%d')
        if date_key in daily_data:
            daily_data[date_key] += session.duration_hours + session.duration_minutes/60
    
    return render_template('analytics.html',
                         weekly_data=weekly_data,
                         subject_data=subject_data,
                         monthly_data=monthly_data,
                         daily_data=daily_data)

@app.route('/goals', methods=['GET', 'POST'])
@login_required
def goals():
    if request.method == 'POST':
        title = request.form.get('title')
        target_hours = int(request.form.get('target_hours', 0))
        goal_type = request.form.get('goal_type', 'daily')
        due_date_str = request.form.get('due_date')
        
        if due_date_str:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        else:
            if goal_type == 'daily':
                due_date = datetime.now(timezone.utc).date()
            else:
                due_date = datetime.now(timezone.utc).date() + timedelta(days=7)
        
        goal = Goal(
            user_id=current_user.id,
            title=title,
            target_hours=target_hours,
            goal_type=goal_type,
            due_date=due_date
        )
        db.session.add(goal)
        db.session.commit()
        flash('Goal created successfully!', 'success')
        return redirect(url_for('goals'))
    
    all_goals = Goal.query.filter_by(user_id=current_user.id).order_by(Goal.created_at.desc()).all()
    return render_template('goals.html', goals=all_goals)

@app.route('/goals/<int:goal_id>/complete', methods=['POST'])
@login_required
def complete_goal(goal_id):
    goal = Goal.query.get_or_404(goal_id)
    if goal.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('goals'))
    
    goal.completed = True
    db.session.commit()
    flash('Goal marked as completed!', 'success')
    return redirect(url_for('goals'))

@app.route('/goals/<int:goal_id>/delete', methods=['POST'])
@login_required
def delete_goal(goal_id):
    goal = Goal.query.get_or_404(goal_id)
    if goal.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('goals'))
    
    db.session.delete(goal)
    db.session.commit()
    flash('Goal deleted.', 'success')
    return redirect(url_for('goals'))

@app.route('/notes', methods=['GET', 'POST'])
@login_required
def notes():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        subject = request.form.get('subject')
        important = request.form.get('important') == 'on'
        
        note = Note(
            user_id=current_user.id,
            title=title,
            content=content,
            subject=subject,
            important=important
        )
        db.session.add(note)
        db.session.commit()
        flash('Note saved successfully!', 'success')
        return redirect(url_for('notes'))
    
    all_notes = Note.query.filter_by(user_id=current_user.id).order_by(Note.updated_at.desc()).all()
    subjects = ['Mathematics', 'Programming', 'Science', 'AI & Machine Learning', 
                'Data Structures', 'Web Development', 'Aptitude', 'Other']
    
    return render_template('notes.html', notes=all_notes, subjects=subjects)

@app.route('/notes/<int:note_id>/toggle_important', methods=['POST'])
@login_required
def toggle_important(note_id):
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('notes'))
    
    note.important = not note.important
    db.session.commit()
    return redirect(url_for('notes'))

@app.route('/notes/<int:note_id>/toggle_revision', methods=['POST'])
@login_required
def toggle_revision(note_id):
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('notes'))
    
    note.revision_completed = not note.revision_completed
    db.session.commit()
    return redirect(url_for('notes'))

@app.route('/notes/<int:note_id>/delete', methods=['POST'])
@login_required
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('notes'))
    
    db.session.delete(note)
    db.session.commit()
    flash('Note deleted.', 'success')
    return redirect(url_for('notes'))

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_profile':
            current_user.email = request.form.get('email')
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        
        elif action == 'change_password':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            
            if bcrypt.check_password_hash(current_user.password, current_password):
                current_user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
                db.session.commit()
                flash('Password changed successfully!', 'success')
            else:
                flash('Current password is incorrect.', 'danger')
        
        elif action == 'reset_data':
            if request.form.get('confirm') == 'DELETE':
                StudySession.query.filter_by(user_id=current_user.id).delete()
                Goal.query.filter_by(user_id=current_user.id).delete()
                Note.query.filter_by(user_id=current_user.id).delete()
                db.session.commit()
                flash('All data has been reset.', 'success')
            else:
                flash('Please type DELETE to confirm.', 'danger')
        
        return redirect(url_for('settings'))
    
    return render_template('settings.html')

@app.route('/export/csv')
@login_required
def export_csv():
    sessions = StudySession.query.filter_by(user_id=current_user.id).order_by(StudySession.date.asc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['Date', 'Subject', 'Hours', 'Minutes', 'Notes'])
    for session in sessions:
        writer.writerow([
            session.date.strftime('%Y-%m-%d'),
            session.subject,
            session.duration_hours,
            session.duration_minutes,
            session.notes or ''
        ])
    
    output.seek(0)
    response = app.response_class(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': 'attachment; filename=study_data.csv'
        }
    )
    return response

# Create database tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
