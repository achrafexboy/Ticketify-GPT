import requests
import base64

class AirtableService:
    def __init__(self, api_key, base_id, table_name):
        self.api_key = api_key
        self.base_id = base_id
        self.table_name = table_name
        self.url = f"https://api.airtable.com/v0/{self.base_id}/{self.table_name}"
        self.semi_url = f"https://api.airtable.com/v0/{self.base_id}/tblbCJ1o8i0qBdfSN"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.upload_url_template = "https://content.airtable.com/v0/{baseId}/{recordId}/{attachmentFieldIdOrName}/uploadAttachment"

    def create_ticket(self, project_name, priority, gpt_response, description, image_paths=[]):
        """
        Creates a ticket in Airtable, then uploads images as attachments.
        """
        data = {
            "fields": {
                "Project Name": project_name,
                "Priority": priority.capitalize(),
                "Gpt's description": gpt_response,
                "Client's description": description
            }
        }

        # Create the record first
        response = requests.post(self.url, headers=self.headers, json=data)

        if response.status_code not in [200, 201]:
            return False, f"Error creating Airtable ticket: {response.json()}"

        record_id = response.json()["id"]  # Get the record ID

        # Upload images one by one
        uploaded_images = []
        for file_path in image_paths:
            file_url = self.upload_attachment(record_id, "Attachments", file_path)
            if file_url:
                uploaded_images.append({"url": file_url})

        # Attach uploaded images to the record
        if uploaded_images:
            update_data = {
                "fields": {
                    "Attachments": uploaded_images
                }
            }
            update_url = f"{self.url}/{record_id}"
            update_response = requests.patch(update_url, headers=self.headers, json=update_data)

            if update_response.status_code not in [200, 201]:
                return False, f"Error attaching images: {update_response.json()}"

        return True, record_id, f"https://airtable.com/{self.base_id}/{self.table_name}/{record_id}"

    def upload_attachment(self, record_id, field_name, file_path):
        """
        Uploads an image as a Base64-encoded file to Airtable.
        """
        url = self.upload_url_template.format(
            baseId=self.base_id, recordId=record_id, attachmentFieldIdOrName=field_name
        )

        try:
            # Convert file to Base64
            with open(file_path, "rb") as file:
                file_content = base64.b64encode(file.read()).decode('utf-8')

            data = {
                "contentType": "image/png",  # Change if needed (jpeg, gif, etc.)
                "file": file_content,
                "filename": file_path.split("\\")[-1]
            }

            response = requests.post(url, headers=self.headers, json=data)

            if response.status_code in [200, 201]:
                return response.json().get("url")  # Airtable returns the uploaded file URL
            else:
                print(f"Error uploading file to Airtable: {response.json()}")
                return None

        except Exception as e:
            print(f"Upload error: {str(e)}")
            return None

    def assign_ticket_to_user(self, record_id, user_id):
        """
        Assign the ticket to the user in Airtable by updating the 'assigned' field.
        """
        try:
            # Make the request to Airtable to update the 'assigned' field
            data = {
                "fields": {
                    "Assigned": user_id  # Assuming "Assigned" field contains the user ID or name
                }
            }
            update_url = f"{self.url}/{record_id}"
            response = requests.patch(update_url, headers=self.headers, json=data)

            if response.status_code in [200, 201]:
                return True, f"Ticket successfully assigned to {user_id}"
            else:
                return False, f"Error assigning ticket in Airtable: {response.json()}"

        except Exception as e:
            return False, f"Error assigning ticket to user: {str(e)}"

    def get_project_attachments(self, project_name):
        """
        Checks if the project name exists in the table and retrieves its 'Cadrage' (attachments) and 'Slack ID' fields.
        """
        query_url = f"{self.semi_url}?filterByFormula={{Name}}='{project_name}'"
        response = requests.get(query_url, headers=self.headers)

        if response.status_code == 200:
            records = response.json().get('records', [])
            if records:
                # Assuming the first matching record is the one we need
                fields = records[0]['fields']
                cadrage_field = fields.get('Cadrage', [])
                slack_id = fields.get('Slack ID', None)
                return cadrage_field, slack_id  # Return both fields
            else:
                return None, None  # No matching project found
        else:
            print(f"Error querying Airtable: {response.json()}")
            return None, None
