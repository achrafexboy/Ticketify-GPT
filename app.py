import os
import uuid
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, session
from werkzeug.utils import secure_filename
from datetime import datetime
from config import Config
from services.openai_service import OpenAIService
from services.slack_service import SlackService

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

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


# File Upload Helper Function
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Main Route (Protected)
@app.route('/', methods=['GET', 'POST'])
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

    return render_template('index.html', config=app.config)

@app.route('/send-to-slack', methods=['POST'])
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

if __name__ == '__main__':
    app.run(debug=True)
