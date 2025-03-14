import os
from dotenv import load_dotenv

load_dotenv('.env.dev')

# Ensure instance directory exists
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
os.makedirs(INSTANCE_DIR, exist_ok=True)  # ✅ Create instance folder if missing

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-secret-key')
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size

    # Authentication settings
    SQLALCHEMY_DATABASE_URI = os.environ.get("DB_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Test mode flag - set to True to use mock responses
    TEST_MODE = os.environ.get('TEST_MODE', 'false').lower() == 'true'

    # OpenAI credentials
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    OPENAI_ASSISTANT_ID = os.environ.get('OPENAI_ASSISTANT_ID')
    
    # Slack credentials
    SLACK_BOT_TOKEN = os.environ.get('SLACK_BOT_TOKEN')
    SLACK_CHANNEL = os.environ.get('SLACK_CHANNEL')