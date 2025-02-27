import os
import time
from openai import OpenAI
from werkzeug.utils import secure_filename

class OpenAIService:
    def __init__(self, api_key, assistant_id):
        self.client = OpenAI(api_key=api_key)
        self.assistant_id = assistant_id
        self.test_mode = api_key == 'test-key-not-real'
    
    def process_request(self, description, image_paths):
        # If in test mode, return a mock response
        if self.test_mode:
            return f"This is a test response. I received: {description[:50]}... and {len(image_paths)} images."
        
        # Create a thread
        thread = self.client.beta.threads.create()
        
        # Add a message to the thread with the description and images
        message_params = {
            "role": "user",
            "content": [{"type": "text", "text": description}]
        }
        
        # Add image file attachments if available
        if image_paths:
            file_ids = []
            for image_path in image_paths:
                if os.path.exists(image_path):
                    file = self.client.files.create(
                        file=open(image_path, "rb"),
                        purpose="assistants"
                    )
                    file_ids.append(file.id)
            
            # Attach files if uploaded
            if file_ids:
                message_params["content"].extend(
                    [{"type": "image_file", "image_file": {"file_id": fid}} for fid in file_ids]
                )
        
        # Add the message to the thread
        self.client.beta.threads.messages.create(
            thread_id=thread.id,
            **message_params
        )
        
        # Run the assistant on the thread
        run = self.client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=self.assistant_id
        )
        
        # Poll for the run completion
        while True:
            run_status = self.client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            if run_status.status == 'completed':
                break
            elif run_status.status in ['failed', 'cancelled', 'expired']:
                return f"Run ended with status: {run_status.status}"
            time.sleep(1)
        
        # Get the assistant's response
        messages = self.client.beta.threads.messages.list(
            thread_id=thread.id
        )
        
        # Return the assistant's latest message
        for message in messages.data:
            if message.role == "assistant":
                return message.content[0].text.value
        
        return "No response from the assistant."