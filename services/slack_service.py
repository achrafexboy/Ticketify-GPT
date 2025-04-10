import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

class SlackService:
    def __init__(self, bot_token, channel):
        self.client = WebClient(token=bot_token)
        self.channel = channel
        self.test_mode = bot_token == 'test-slack-token'

    def send_message(self, message, record_id, link_airtable, image_paths=None):
        """
        Sends a Slack message with text and a button to accept the ticket.
        """
        if self.test_mode:
            print(f"[TEST MODE] Would send to Slack: {message[:100]}...")
            return True, "Message would be sent to Slack (test mode)"

        try:
            # Send the text message with the "Accept Ticket" button
            message_response = self.client.chat_postMessage(
                channel=self.channel,
                text=message,
                metadata={
                    "event_type": "ticket_created",
                    "event_payload": {
                        "record_id": record_id,
                        "ticket_url": f"{link_airtable}"
                    }
                },
                blocks=[
                    {
                        "type": "section",
                        "block_id": "ticket_details",
                        "text": {
                            "type": "mrkdwn",
                            "text": message
                        },
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "Accept Ticket"
                                },
                                "action_id": "accept_ticket",
                                "value": record_id,
                                "style": "primary"
                            }
                        ]
                    }
                ]
            )

            # Upload images if available
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

    def send_direct_message(self, slack_id, message):
        """
        Sends a direct message to a user identified by their Slack ID.
        """
        if self.test_mode:
            print(f"[TEST MODE] Would send DM to {slack_id}: {message[:100]}...")
            return True, "Direct message would be sent to Slack (test mode)"

        try:
            response = self.client.chat_postMessage(
                channel=slack_id,
                text=message
            )
            return True, "Direct message sent successfully"
        except SlackApiError as e:
            return False, f"Error sending direct message to Slack: {e.response['error']}"
    
    def update_ticket_status(self, ticket_url, user_id, message_ts):
        """
        Update the Slack message to show the user who accepted the ticket.
        Replaces the "Accept Ticket" button with a message showing who accepted it.
        """
        try:
            # Format the message to show the user who accepted the ticket
            updated_message = f"Ticket has been accepted by <@{user_id}>.\nLink: {ticket_url}"

            # Update the message to replace the button
            self.client.chat_update(
                channel=self.channel,
                ts=message_ts,
                text=updated_message,
                blocks=[
                    {
                        "type": "section",
                        "block_id": "ticket_details",
                        "text": {
                            "type": "mrkdwn",
                            "text": updated_message
                        },
                    }
                ]
            )

            return True, f"Ticket accepted by <@{user_id}>."

        except SlackApiError as e:
            return False, f"Error updating message: {e.response['error']}"
