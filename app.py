import os
import uuid
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from config import Config
from services.openai_service import OpenAIService
from services.slack_service import SlackService

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize database and login manager
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize services
openai_service = OpenAIService(
    app.config['OPENAI_API_KEY'],
    app.config['OPENAI_ASSISTANT_ID']
)

slack_service = SlackService(
    app.config['SLACK_BOT_TOKEN'],
    app.config['SLACK_CHANNEL']
)

# User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)  # ✅ Email for login
    username = db.Column(db.String(50), unique=True, nullable=False)  # ✅ Separate username
    password_hash = db.Column(db.String(128), nullable=False)
    poste = db.Column(db.String(20), nullable=False)  # ✅ New Role Field (Dev, PM, QA, Client)
    email_notifications = db.Column(db.Boolean, default=True)  # Default: Enabled

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Submission Model
class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Flask-Login User Loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash("Invalid email or password", "danger")

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        poste = request.form.get('poste')  # ✅ Get user role
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Check if email is already registered
        if User.query.filter_by(email=email).first():
            flash('Email is already registered. Please log in.', 'danger')
            return redirect(url_for('register'))

        # Validate password confirmation
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register'))

        # Ensure a valid poste (role)
        allowed_postes = ['dev', 'pm', 'qa', 'client']
        if poste not in allowed_postes:
            flash('Invalid role selection.', 'danger')
            return redirect(url_for('register'))

        # Create new user
        new_user = User(email=email, username=username, poste=poste)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


# File Upload Helper Function
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/delete-submission/<int:submission_id>', methods=['DELETE'])
@login_required
def delete_submission(submission_id):
    submission = Submission.query.get(submission_id)

    if not submission or submission.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Submission not found or unauthorized'}), 403

    db.session.delete(submission)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Submission deleted successfully'})

@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    if request.method == 'POST':
        new_username = request.form.get('username')
        new_poste = request.form.get('poste')

        # Check if username is taken (excluding the current user)
        existing_user = User.query.filter(User.username == new_username, User.id != current_user.id).first()
        if existing_user:
            flash("This username is already taken. Please choose another.", "danger")
            return redirect(url_for('account'))

        # Update user information
        current_user.username = new_username
        current_user.poste = new_poste
        db.session.commit()

        flash("Your account information has been updated!", "success")
        return redirect(url_for('account'))

    return render_template('account.html')


@app.route('/change-password', methods=['POST'])
@login_required
def change_password():
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    # Check if the old password matches
    if not current_user.check_password(old_password):
        flash("Incorrect current password.", "danger")
        return redirect(url_for('account', section='password'))

    # Validate new password strength
    if len(new_password) < 8 or not any(char.isdigit() for char in new_password) or not any(char.isupper() for char in new_password) or not any(char in "@$!%*?&" for char in new_password):
        flash("New password must be at least 8 characters long, contain a number, an uppercase letter, and a special character.", "danger")
        return redirect(url_for('account', section='password'))

    # Check if new password matches confirmation
    if new_password != confirm_password:
        flash("New passwords do not match.", "danger")
        return redirect(url_for('account', section='password'))

    # Update password
    current_user.set_password(new_password)
    db.session.commit()
    
    flash("Your password has been updated successfully!", "success")
    return redirect(url_for('account'))

# Change notification preferences
@app.route('/edit-notification', methods=['POST'])
@login_required
def edit_notification():
    data = request.get_json()
    if "email_notifications" in data:
        current_user.email_notifications = data["email_notifications"]
        db.session.commit()
        return jsonify({"success": True, "message": "Notification preferences updated"})
    return jsonify({"success": False, "message": "Invalid request"}), 400

# Main Route (Protected)
@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        if 'photos' not in request.files:
            flash('No file part')
            return redirect(request.url)

        description = request.form.get('description', '')
        photos = request.files.getlist('photos')

        if not description and photos[0].filename == '':
            flash('No description or photos provided')
            return redirect(request.url)

        # Save uploaded files
        image_paths = []
        for photo in photos:
            if photo and allowed_file(photo.filename):
                filename = secure_filename(f"{uuid.uuid4()}_{photo.filename}")
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                photo.save(file_path)
                image_paths.append(file_path)

        # Store submission in DB
        new_submission = Submission(user_id=current_user.id, description=description)
        db.session.add(new_submission)
        db.session.commit()

        # Process with OpenAI
        assistant_response = openai_service.process_request(description, image_paths)
        print(assistant_response)

        # Store response in session
        session['assistant_response'] = assistant_response
        session['image_paths'] = image_paths

        return jsonify({
            'success': True,
            'assistant_response': assistant_response
        })

    return render_template('index.html', config=app.config, submissions=Submission.query.filter_by(user_id=current_user.id).order_by(Submission.id.desc()).all())

@app.route('/send-to-slack', methods=['POST'])
@login_required
def send_to_slack():
    data = request.get_json()
    edited_response = data.get('edited_response', '')
    priority = data.get('priority', 'normal')  # ✅ Capture priority from request
    image_paths = session.get('image_paths', [])

    if not edited_response:
        return jsonify({
            'success': False,
            'message': 'No response provided.'
        })
    # Format message with priority
    priority_emoji = {"urgent": "🟥", "normal": "🟨", "low": "🟦"}
    formatted_message = f"{priority_emoji.get(priority, '🟨')} *Priority: {priority.capitalize()}*\n\n{edited_response}"

    # Send the edited response to Slack
    success, message = slack_service.send_message(formatted_message, image_paths)

    if success:
        session.pop('assistant_response', None)
        session.pop('image_paths', None)

    return jsonify({
        'success': success,
        'message': message
    })

@app.route('/get-submissions')
@login_required
def get_submissions():
    user_submissions = Submission.query.filter_by(user_id=current_user.id).order_by(Submission.created_at.desc()).all()
    
    return jsonify([
        {'description': sub.description, 'created_at': sub.created_at.strftime('%Y-%m-%d %H:%M:%S')}
        for sub in user_submissions
    ])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure the database tables are created
    app.run(debug=True)
