import msal
import logging

class PBI_GetAccessToken:
    def __init__(self):
        # Setting up a logger for this class
        self.logger = logging.getLogger(__name__)

    def as_service_principal(self, tenant_id, client_id, akv_url, akv_secret_name):
        """
        Authenticates as a service principal using client credentials.

        This method retrieves a client secret from Azure Key Vault and uses it
        to authenticate with Microsoft Azure as a service principal, obtaining
        an access token for Power BI.

        Parameters:
            tenant_id (str): Azure tenant ID.
            client_id (str): Azure client ID.
            akv_url (str): Azure Key Vault URL.
            akv_secret_name (str): Name of the secret in Azure Key Vault.

        Returns:
            str: An access token for Power BI API.

        Raises:
            Exception: If the authentication fails or any other error occurs.
        """
        try:
            # Retrieve the client secret from Azure Key Vault
            client_secret = mssparkutils.credentials.getSecret(akv_url, akv_secret_name)

            # Setting the authority URL for Azure AD
            authority_url = f"https://login.microsoftonline.com/{tenant_id}/"
            # The scope for Power BI API
            scope = ["https://analysis.windows.net/powerbi/api/.default"]
            
            # Creating an MSAL application instance
            app = msal.ConfidentialClientApplication(
                client_id,
                authority=authority_url,
                validate_authority=True,
                client_credential=client_secret
            )
            
            # Acquiring the token for the client
            result = app.acquire_token_for_client(scopes=scope)
            
            # Checking if the access token is in the result
            if "access_token" in result:
                return result["access_token"]
            else:
                # Log and raise an error if no access token is found
                error_msg = f"Error in getAccessToken: {result.get('error')}, {result.get('error_description')}"
                self.logger.error(error_msg)
                raise Exception(error_msg)
        except Exception as e:
            # Log and re-raise any exceptions that occur
            self.logger.error(f"Error in as_service_principal: {str(e)}")
            raise

    def as_fabric_notebook_owner(self):
        """
        Retrieves an access token as the notebook owner in Fabric.

        This method obtains an access token for Power BI by using the mssparkutils function, 
        assuming that the notebook is running as a Fabric notebook.

        Returns:
            str: An access token for Power BI API.

        Raises:
            Exception: If retrieving the access token fails.
        """
        try:
            # Get the access token using Databricks utilities
            access_token = mssparkutils.credentials.getToken("pbi")
            return access_token
        except Exception as e:
            # Log and re-raise any exceptions that occur
            self.logger.error(f"Error in as_fabric_notebook_owner: {str(e)}")
            raise
