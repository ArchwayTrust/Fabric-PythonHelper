import msal
import logging

class PBI_GetAccessToken:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def as_service_principal(self, tenant_id, client_id, akv_url, akv_secret_name):
        try:
            client_secret = mssparkutils.credentials.getSecret(akv_url, akv_secret_name)

            authority_url = f"https://login.microsoftonline.com/{tenant_id}/"
            scope = ["https://analysis.windows.net/powerbi/api/.default"]
            
            app = msal.ConfidentialClientApplication(
                client_id,
                authority=authority_url,
                validate_authority=True,
                client_credential=client_secret
            )
            
            result = app.acquire_token_for_client(scopes=scope)
            
            if "access_token" in result:
                return result["access_token"]
            else:
                error_msg = f"Error in getAccessToken: {result.get('error')}, {result.get('error_description')}"
                self.logger.error(error_msg)
                raise Exception(error_msg)
        except Exception as e:
            self.logger.error(f"Error in as_service_principal: {str(e)}")
            raise

    def as_fabric_notebook_owner(self):
        try:
            access_token = mssparkutils.credentials.getToken("pbi")
            return access_token
        except Exception as e:
            self.logger.error(f"Error in as_fabric_notebook_owner: {str(e)}")
            raise