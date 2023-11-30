import msal
import requests
import json
import base64
import time

class GraphAPI_Emails:
    REDIRECT_URI = "https://login.microsoftonline.com/common/oauth2/nativeclient"
    SCOPES = ["User.Read", "Mail.ReadWrite"]

    def __init__(self, tennant_id, client_id, akv_url, refresh_secret_name):
        self.tennant_id = tennant_id,
        self.client_id = client_id,
        self.akv_url = akv_url # Url for Azure Key Vault in form https://{key_vault_name}.vault.azure.net/
        self.refresh_secret_name = refresh_secret_name # This will hold the refresh secret for the authenticated user.
        
        # Initialize the MSAL confidential client
        self.app = msal.PublicClientApplication(
                    client_id = self.CLIENT_ID,
                    authority = f"https://login.microsoftonline.com/{self.tennant_id}"
        )

        try:
            # Get latest refresh token
            self.refresh_token = mssparkutils.credentials.getSecret(self.AKV_URL, self.refresh_secret_name)

            # Get access token and a new refresh token.
            response = self.app.acquire_token_by_refresh_token(self.refresh_token, self.SCOPES)
            self.access_token = response["access_token"]
            self.new_refresh_token = response["refresh_token"]
            self.store_refresh_token(self.new_refresh_token)
        except:
            self.access_token = None
            self.new_refresh_token = None
            print("Couldn't get access token. Try running get_initial_tokens")
    
    def store_refresh_token(self, refresh_token):
        # Get credentials for key vault using workbook owner.
        akv_cred = mssparkutils.credentials.getToken('keyvault')

        # Prepare the URL and headers
        url = f"{self.AKV_URL}/secrets/{self.refresh_secret_name}?api-version=7.4"
        headers = {"Authorization": f"Bearer {akv_cred}",
                    "Content-Type": "application/json"}

        # Prepare the data
        data = json.dumps({"value": refresh_token})

        # Make the PUT request
        response = requests.put(url, headers=headers, data=data)

        # Check response
        if response.status_code == 200:
            print("Secret updated successfully.")
        else:
            print("Failed to update secret.")
            print("Status code:", response.status_code)
            print("Response:", response.text)


    def get_initial_tokens(self):
        flow = self.app.initiate_device_flow(scopes=self.SCOPES)
        if "user_code" not in flow:
            raise ValueError("Fail to create device flow. Err: %s" % json.dumps(flow, indent=4))
        flow['expires_at']=int(time.time())+60 # Wait a maximum of 60 seconds.
        print(flow["message"])

        result = self.app.acquire_token_by_device_flow(flow)
        if "access_token" in result:
            print("Successfully authenticated.")
            self.access_token = result['access_token']
            self.refresh_token = result['refresh_token']
            self.store_refresh_token(result['refresh_token'])
        else:
            print("Authentication failed. Result was: %s" % result)

    # Function to search message by subject
    def search_message_by_subject(self, user_id, subject, sender_email):
        headers = {'Authorization': f'Bearer {self.access_token}'}
        endpoint = f'https://graph.microsoft.com/v1.0/users/{user_id}/messages'
        query_parameters = {
            '$filter': f"subject eq '{subject}' and from/emailAddress/address eq '{sender_email}'",
            '$select': 'id,subject,from'
        }
        response = requests.get(endpoint, headers=headers, params=query_parameters)
        
        if response.status_code == 200:
            # Assuming the subject is unique and only one message has this subject
            messages = response.json().get('value', [])
            if messages:
                return messages[0]['id']  # Return the ID of the first message found
            else:
                return None
        else:
            raise Exception(f"Error searching message by subject: {response.json()}")
        
    # Function to get list of attachments in an email
    def get_attachment_ids_and_names(self, message_id):
        # The URL for the attachments endpoint
        url = f'https://graph.microsoft.com/v1.0/me/messages/{message_id}/attachments'

        # Set the OAuth token in the header
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

        # Perform the GET request to retrieve the attachments
        response = requests.get(url, headers=headers)

        # Initialize an empty list to hold attachment IDs and names
        attachments_info = []

        # Check if the request was successful
        if response.status_code == 200:
            # Parse the JSON response
            attachments = response.json()
            
            # Extract the attachment IDs and names
            attachments_info = [
                (attachment['id'], attachment['name'])
                for attachment in attachments.get('value', [])
            ]
        else:
            # Raise an exception if the call was unsuccessful
            response.raise_for_status()

        return attachments_info
    
    # Use Microsoft Graph API to fetch email and download attachment
    # This decodes to a stirng and ONLY works with csv/text.
    def download_attachment(self, user_id, message_id, attachment_id):
        headers = {'Authorization': 'Bearer ' + self.access_token}
        attachment_url = f'https://graph.microsoft.com/v1.0/users/{user_id}/messages/{message_id}/attachments/{attachment_id}'
        attachment_r = requests.get(attachment_url, headers=headers)
        attachment = attachment_r.json()
        attachment_contents = base64.b64decode(attachment['contentBytes']).decode('utf-8')
        return attachment_contents
    
    # Function to delete email
    def delete_email(self, user_id, message_id):
        """
        Deletes an email using the Microsoft Graph API.

        :param access_token: A valid OAuth access token with permissions to delete emails.
        :param user_id: The ID of the user who owns the message.
        :param message_id: The ID of the message to be deleted.
        :return: True if the email was successfully deleted, False otherwise.
        """
        
        # The URL for the delete message endpoint
        delete_url = f'https://graph.microsoft.com/v1.0/users/{user_id}/messages/{message_id}'

        # Set the OAuth token in the header
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

        # Perform the DELETE request
        response = requests.delete(delete_url, headers=headers)

        # Return True if the status code indicates success (204 No Content), False otherwise
        return response.status_code == 204

    def interactive(self):
        result = self.app.acquire_token_interactive(scopes=self.SCOPES, redirect_uri=self.REDIRECT_URI)