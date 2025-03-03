import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

class SlackService:
    def __init__(self, bot_token, channel):
        self.client = WebClient(token=bot_token)
        self.channel = channel
        self.test_mode = bot_token == 'test-slack-token'

    def send_message(self, message, image_paths=None):
        """
        Sends a Slack message with text first, then attaches all images in one request.
        """
        if self.test_mode:
            print(f"[TEST MODE] Would send to Slack: {message[:100]}...")
            return True, "Message would be sent to Slack (test mode)"

        try:
            # ✅ **Step 1: Send the text message first**
            message_response = self.client.chat_postMessage(
                channel=self.channel,
                text=message
            )

            # ✅ **Step 2: Upload ALL images in one request**
            if image_paths:
                file_upload_responses = self.client.files_upload_v2(
                    channels=self.channel,
                    file_uploads=[
                        {"file": open(image_path, "rb")} for image_path in image_paths if os.path.exists(image_path)
                    ],
                    initial_comment="📎 Attached Images:"
                )

                if not file_upload_responses["ok"]:
                    return False, f"Error uploading images: {file_upload_responses['error']}"

            return True, "Message and images sent successfully"

        except SlackApiError as e:
            return False, f"Error sending message to Slack: {e.response['error']}"
