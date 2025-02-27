import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

class SlackService:
    def __init__(self, bot_token, channel):
        self.client = WebClient(token=bot_token)
        self.channel = channel
        self.test_mode = bot_token == 'test-slack-token'
    
    def send_message(self, message, image_paths=None):
        # If in test mode, just simulate success
        if self.test_mode:
            print(f"[TEST MODE] Would send to Slack: {message[:100]}...")
            return True, "Message would be sent to Slack (test mode)"
        
        try:
            # Upload images first if they exist
            file_ids = []
            if image_paths:
                for image_path in image_paths:
                    if os.path.exists(image_path):
                        response = self.client.files_upload_v2(
                            file=image_path,
                            channel=self.channel
                        )
                        if response["files"]:
                            file_ids.append(response["files"][0]["id"])
            
            # Send the text message
            response = self.client.chat_postMessage(
                channel=self.channel,
                text=message,
                file_ids=file_ids if file_ids else None
            )
            return True, "Message sent successfully"
        except SlackApiError as e:
            return False, f"Error sending message to Slack: {e.response['error']}"