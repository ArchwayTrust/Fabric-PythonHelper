import msal
import requests
import json
import base64
import time
from notebookutils import mssparkutils

class Emails:
    """
    A class to interact with Microsoft Graph API for managing emails.

    Attributes:
        tennant_id (str): Tenant ID for Azure authentication.
        client_id (str): Client ID for Azure authentication.
        akv_url (str): Azure Key Vault URL, in the form https://{key_vault_name}.vault.azure.net/.
        refresh_secret_name (str): Name of the secret in the Azure Key Vault that holds the refresh token.
        app (msal.PublicClientApplication): MSAL instance for Azure authentication.
        access_token (str): Token for authenticated access to the Graph API.
        new_refresh_token (str): New refresh token received after successful authentication.
    """

    REDIRECT_URI = "https://login.microsoftonline.com/common/oauth2/nativeclient"
    SCOPES = ["User.Read", "Mail.ReadWrite"]

    def __init__(self, tennant_id, client_id, akv_url, refresh_secret_name):
        """
        Initializes the GraphAPI_Emails class with required Azure and Graph API parameters.

        Parameters:
            tennant_id (str): Tenant ID for Azure authentication.
            client_id (str): Client ID for Azure authentication.
            akv_url (str): Azure Key Vault URL.
            refresh_secret_name (str): Name of the secret in the Azure Key Vault.
        """
        self.tennant_id = tennant_id
        self.client_id = client_id
        self.akv_url = akv_url  # URL for Azure Key Vault
        self.refresh_secret_name = refresh_secret_name  # Refresh secret name in the Azure Key Vault
        
        # Initialize the MSAL confidential client
        self.app = msal.PublicClientApplication(
            client_id=self.client_id,
            authority=f"https://login.microsoftonline.com/{self.tennant_id}"
        )

        try:
            # Get latest refresh token
            self.refresh_token = mssparkutils.credentials.getSecret(self.akv_url, self.refresh_secret_name)

            # Get access token and a new refresh token.
            response = self.app.acquire_token_by_refresh_token(self.refresh_token, self.SCOPES)
            self.access_token = response["access_token"]
            self.new_refresh_token = response["refresh_token"]
            self._store_refresh_token(self.new_refresh_token)
        except Exception as e:
            self.access_token = None
            self.new_refresh_token = None
            print("Couldn't get access token. Try running get_initial_tokens")
            print(f"Error: {e}")
    
    def _store_refresh_token(self, refresh_token):
        """
        Stores the given refresh token in the Azure Key Vault.

        This method updates the Azure Key Vault secret with the new refresh token
        for future authentications.

        Parameters:
            refresh_token (str): The refresh token to be stored in the Azure Key Vault.
        """
        # Get credentials for key vault using workbook owner.
        akv_cred = mssparkutils.credentials.getToken('keyvault')

        # Prepare the URL and headers for the Azure Key Vault request
        url = f"{self.akv_url}/secrets/{self.refresh_secret_name}?api-version=7.4"
        headers = {
            "Authorization": f"Bearer {akv_cred}",
            "Content-Type": "application/json"
        }

        # Convert the refresh token to a JSON formatted string
        data = json.dumps({"value": refresh_token})

        # Make the PUT request to the Azure Key Vault to update the secret
        response = requests.put(url, headers=headers, data=data)

        # Check the response from the Azure Key Vault
        if response.status_code == 200:
            print("Secret updated successfully.")
        else:
            print("Failed to update secret.")
            print("Status code:", response.status_code)
            print("Response:", response.text)


    def get_initial_tokens(self):
        """
        Initiates the device flow to acquire initial access and refresh tokens.

        This method uses MSAL to start a device flow authentication, printing out
        a user code and waiting for the user to authenticate. If successful, it 
        stores the new access token and refresh token.
        """
        # Initiate the device flow with specified scopes
        flow = self.app.initiate_device_flow(scopes=self.SCOPES)

        # Check if the user_code is part of the flow response
        if "user_code" not in flow:
            raise ValueError(f"Fail to create device flow. Err: {json.dumps(flow, indent=4)}")

        # Set an expiration time for the flow (60 seconds from now)
        flow['expires_at'] = int(time.time()) + 60

        # Display the authentication message to the user
        print(flow["message"])

        # Attempt to acquire the token by the device flow
        result = self.app.acquire_token_by_device_flow(flow)

        # Check if the authentication was successful
        if "access_token" in result:
            print("Successfully authenticated.")
            # Store the access token and refresh token from the result
            self.access_token = result['access_token']
            self.refresh_token = result['refresh_token']
            # Store the new refresh token in the key vault
            self._store_refresh_token(result['refresh_token'])
        else:
            # Handle authentication failure
            print(f"Authentication failed. Result was: {result}")

    def search_message_by_subject(self, user_id, subject, sender_email):
        """
        Searches for an email by its subject and sender's email using Microsoft Graph API.

        This method queries the Microsoft Graph API to find an email that matches
        the given subject and sender's email address. It returns the ID of the first
        matching email if found.

        Parameters:
            user_id (str): The ID of the user whose mailbox is being searched.
            subject (str): The subject of the email to search for.
            sender_email (str): The email address of the sender of the email.

        Returns:
            str: The ID of the first email that matches the search criteria, or None if no match is found.
        """
        # Setting up the authorization header with the access token
        headers = {'Authorization': f'Bearer {self.access_token}'}

        # The endpoint URL for Microsoft Graph API to access user's messages
        endpoint = f'https://graph.microsoft.com/v1.0/users/{user_id}/messages'

        # Setting query parameters for filtering by subject and sender's email
        query_parameters = {
            '$filter': f"subject eq '{subject}' and from/emailAddress/address eq '{sender_email}'",
            '$select': 'id,subject,from'
        }

        # Making a GET request to the Graph API
        response = requests.get(endpoint, headers=headers, params=query_parameters)

        # Checking the response status code
        if response.status_code == 200:
            # Parsing the response to get messages
            messages = response.json().get('value', [])
            # Return the ID of the first message found if messages are present
            return messages[0]['id'] if messages else None
        else:
            # Raising an exception if the API call was unsuccessful
            raise Exception(f"Error searching message by subject: {response.json()}")
        
    def get_attachment_ids_and_names(self, message_id):
        """
        Retrieves a list of attachment IDs and names for a specified email message.

        This method uses the Microsoft Graph API to fetch all attachments for a given
        email message. It returns a list of tuples, each containing the ID and name of
        an attachment.

        Parameters:
            message_id (str): The ID of the email message whose attachments are to be retrieved.

        Returns:
            list of tuple: A list of tuples, where each tuple contains the ID and name of an attachment.
        """
        # Constructing the URL for the Microsoft Graph API attachments endpoint
        url = f'https://graph.microsoft.com/v1.0/me/messages/{message_id}/attachments'

        # Setting up the authorization header with the access token
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

        # Performing a GET request to retrieve the attachments
        response = requests.get(url, headers=headers)

        # Initializing an empty list to store attachment information
        attachments_info = []

        # Checking the response status code
        if response.status_code == 200:
            # Parsing the JSON response to extract attachment data
            attachments = response.json()
            
            # Extracting attachment IDs and names and adding them to the list
            attachments_info = [
                (attachment['id'], attachment['name'])
                for attachment in attachments.get('value', [])
            ]
        else:
            # Raising an exception if the API call was unsuccessful
            response.raise_for_status()

        return attachments_info
    
    def download_attachment(self, user_id, message_id, attachment_id, is_binary=False, encoding='utf-8'):
        """
        Downloads an attachment from an email using the Microsoft Graph API.

        This method fetches an attachment from a specific email. It can handle both
        binary files (like images or PDFs) and text-based files (like CSV or TXT).

        Parameters:
            user_id (str): The ID of the user who owns the message.
            message_id (str): The ID of the message from which the attachment is to be downloaded.
            attachment_id (str): The ID of the attachment to be downloaded.
            is_binary (bool): Flag indicating whether the attachment is a binary file. Default is False.
            encoding (str): The encoding used to decode the attachment's content. Ignored if is_binary is True. Default is 'utf-8'.

        Returns:
            bytes or str: The content of the attachment, either as a byte string (for binary files) or a decoded string (for text files).
        """
        # Setting up the authorization header with the access token
        headers = {'Authorization': f'Bearer {self.access_token}'}

        # Constructing the URL to access the attachment via Microsoft Graph API
        attachment_url = f'https://graph.microsoft.com/v1.0/users/{user_id}/messages/{message_id}/attachments/{attachment_id}'

        # Making a GET request to fetch the attachment
        attachment_response = requests.get(attachment_url, headers=headers)

        # Extracting the attachment content from the response
        attachment = attachment_response.json()
        attachment_content = base64.b64decode(attachment['contentBytes'])

        # Returning the attachment content based on its type
        return attachment_content if is_binary else attachment_content.decode(encoding)

    def delete_email(self, user_id, message_id):
        """
        Deletes an email using the Microsoft Graph API.

        This method sends a DELETE request to the Microsoft Graph API to remove an
        email message from a user's mailbox. It uses the user's ID and the message's
        ID to identify the specific email to be deleted.

        Parameters:
            user_id (str): The ID of the user who owns the message.
            message_id (str): The ID of the message to be deleted.

        Returns:
            bool: True if the email was successfully deleted, False otherwise.
        """

        # Constructing the URL for the Microsoft Graph API delete message endpoint
        delete_url = f'https://graph.microsoft.com/v1.0/users/{user_id}/messages/{message_id}'

        # Setting up the authorization header with the access token
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

        # Performing the DELETE request to the Graph API
        response = requests.delete(delete_url, headers=headers)

        # Checking if the status code indicates success (204 No Content)
        return response.status_code == 204

    
