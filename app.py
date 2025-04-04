import os
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, request
from werkzeug.utils import secure_filename
from config import Config
from services.openai_service import OpenAIService
from services.slack_service import SlackService
from services.airtable_service import AirtableService
import uuid
import json

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize services
openai_service = OpenAIService(
    app.config['OPENAI_API_KEY'],
    app.config['OPENAI_ASSISTANT_ID']
)

slack_service = SlackService(
    app.config['SLACK_BOT_TOKEN'],
    app.config['SLACK_CHANNEL']
)

airtable_service = AirtableService(
    api_key=app.config['AIRTABLE_API_KEY'],
    base_id=app.config['AIRTABLE_BASE_ID'],
    table_name=app.config['AIRTABLE_TABLE_NAME']
)

# Slack interaction route to capture the button click
@app.route('/slack/actions', methods=['POST'])
def slack_actions():
    # Parse the incoming payload from Slack's interactive message
    payload = request.form.get('payload')
    if not payload:
        return jsonify({'text': 'No payload received!'}), 400
    
    data = json.loads(payload)
    actions = data.get('actions', [])
    
    # Check if the "Accept Ticket" button was clicked
    if actions:
        action = actions[0]
        if action.get('action_id') == 'accept_ticket':
            ticket_url = data["message"]["attachments"][0]["original_url"] # The ticket URL passed with the button
            ticket_id = action.get('value')  # The ticket ID passed with the button
            user_id = data.get('user', {}).get('name')  # The user who clicked the button
            message_ts = data.get('message', {}).get('ts')  # The timestamp of the original message
            
            # Call SlackService to update the ticket status
            success, response = slack_service.update_ticket_status(ticket_url, user_id, message_ts)
            if success:
                # Call AirtableService to update the "assigned" field for the ticket
                airtable_success, airtable_response = airtable_service.assign_ticket_to_user(ticket_id, user_id)
                if airtable_success:
                    return jsonify({
                        'response_action': 'update',
                        'text': f"Ticket has been accepted by <@{user_id}> and assigned successfully."
                    })
                else:
                    return jsonify({'text': f"Error assigning ticket in Airtable: {airtable_response}"}), 400
            else:
                return jsonify({'text': response}), 400
    
    return jsonify({'text': 'Action not recognized!'}), 400

# File Upload Helper Function
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'photos' not in request.files:
            return jsonify({"success": False, "message": "No file part"})

        project_name = request.form.get('project_name', '')
        description = request.form.get('description', '')
        priority = request.form.get('priority', 'normal')
        photos = request.files.getlist('photos')

        if not description and photos[0].filename == '':
            return jsonify({"success": False, "message": "No description or photos provided"})

        # Save uploaded files
        image_paths = []
        for photo in photos:
            if photo and allowed_file(photo.filename):
                filename = secure_filename(f"{uuid.uuid4()}_{photo.filename}")
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                photo.save(file_path)
                image_paths.append(file_path)

        # Process AI Request
        full_request = f"Project: {project_name}\nPriority: {priority.capitalize()}\n\n{description}"
        assistant_response = openai_service.process_request(full_request, image_paths)

        # Create Ticket in Airtable with Image Uploads
        _, record_id, link = airtable_service.create_ticket(project_name, priority, assistant_response, description, image_paths)

        # Send to Slack
        priority_emoji = {"urgent": "🟥", "normal": "🟨", "faible": "🟦"}
        formatted_message = f"📌 *Project: {project_name}*\n{priority_emoji.get(priority, '🟨')} *Priority: {priority.capitalize()}*\n*Link:* {link}\n\n{assistant_response}\n"
        slack_service.send_message(formatted_message, record_id, image_paths)

        return jsonify({"success": True})

    return render_template('index.html', config=app.config)

if __name__ == '__main__':
    app.run(debug=True)
