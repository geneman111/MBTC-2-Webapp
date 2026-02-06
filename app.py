import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'office-secret-key-123' # Keeps sessions secure

# --- DATABASE SETUP ---
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'office.db')
db = SQLAlchemy(app)

# --- LOGIN MANAGER ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- MODELS ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    role = db.Column(db.String(20), default='User') # Owner, Core, User
    group_name = db.Column(db.String(50))

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    response = db.Column(db.String(100))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- ROUTES ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form.get('username')
        user = User.query.filter_by(name=name).first()
        if user:
            login_user(user, remember=True) # "remember=True" saves the login info
            return redirect(url_for('index'))
        flash('Name not found. Please contact Admin.')
    return render_template('login.html')

@app.route('/')
@login_required
def index():
    # Only show tasks this user hasn't finished
    done_ids = [s.task_id for s in Submission.query.filter_by(user_id=current_user.id).all()]
    pending_tasks = Task.query.filter(~Task.id.in_(done_ids)).all()
    return render_template('index.html', user=current_user, tasks=pending_tasks)

@app.route('/submit', methods=['POST'])
@login_required
def submit():
    task_id = request.form.get('task_id')
    response = request.form.get('response')
    new_sub = Submission(user_id=current_user.id, task_id=task_id, response=response)
    db.session.add(new_sub)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- DB INITIALIZATION ---
with app.app_context():
    db.create_all()
    # Create a test user if none exists
    if not User.query.filter_by(name="Admin").first():
        db.session.add(User(name="Admin", role="Owner", group_name="HQ"))
        db.session.add(Task(title="Strength for 10 March"))
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True, port=5000)