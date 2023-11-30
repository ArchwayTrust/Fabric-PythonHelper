import requests
import json
import time

class SemanticModelRefresher:
    # Base URL for Power BI API calls
    BASE_URL = "https://api.powerbi.com/v1.0/myorg/datasets/"

    def __init__(self, semantic_model_id, access_token, refresh_body={"notifyOption": "NoNotification"}):
        """
        Initializes the SemanticModelRefresher instance.

        Parameters:
            semantic_model_id (str): The ID of the semantic model to be refreshed.
            access_token (str): Access token for Power BI API authentication.
            refresh_body (dict): The request body for the refresh, defaults to no notification.
        """
        self.semantic_model_id = semantic_model_id
        self.access_token = access_token
        self.refresh_body = refresh_body

    def _send_refresh_request(self):
        """
        Sends a refresh request to the Power BI API for the specified semantic model.

        Returns:
            Response: The response object from the requests.post call.
        """
        # Constructing the refresh endpoint URL
        refresh_endpoint = f"{self.BASE_URL}{self.semantic_model_id}/refreshes"
        
        # Setting up the request headers
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        # Making a POST request to start the refresh
        response = requests.post(refresh_endpoint, headers=headers, json=self.refresh_body)
        response.raise_for_status()  # Raises an HTTPError for failed requests
        
        return response

    def _handle_refresh_trigger_response(self, response):
        """
        Handles the response from the refresh request.

        Parameters:
            response (Response): The response object from the refresh request.

        Returns:
            str: The result of handling the refresh request.
        """
        if response.ok:
            print("Refresh requested successfully. Waiting for expected duration...")
            return "Refresh started"
        elif response.status_code == 404:
            error_message = "Resource Not Found. Check the Semantic Model ID."
            print(error_message)
            raise Exception(f"Refresh Request Failed: {error_message}")
        else:
            error_message = f"Request failed with status code: {response.status_code}"
            print(error_message)
            raise Exception(f"Refresh Request Failed: {error_message}")

    def _get_refresh_status(self):
        """
        Gets the refresh status of the semantic model.

        Returns:
            dict: The JSON response from the refresh status request.
        """
        # Constructing the refresh status endpoint URL
        refresh_endpoint = f"{self.BASE_URL}{self.semantic_model_id}/refreshes"
        
        # Setting up the request headers
        headers = {
            "Authorization": f"Bearer {self.access_token}",
        }

        # Making a GET request to retrieve the refresh status
        response = requests.get(refresh_endpoint, headers=headers)
        response.raise_for_status()
        
        return response.json()

    def _handle_refresh_status_response(self, response):
        """
        Handles the refresh status response from the Power BI API.

        Parameters:
            response (Response): The response object from the refresh status request.

        Returns:
            dict: The JSON response containing the refresh status.
        """
        try:
            if response.ok:
                return response.json()
            else:
                error_message = f"Refresh Status Request failed with status code: {response.status_code}"
                print(error_message)
                raise Exception(f"Refresh Request Failed: {error_message}")
        except json.JSONDecodeError:
            error_message = f"Invalid JSON response. Status Code: {response.status_code}. Response Text: {response.text}"
            print(error_message)
            raise Exception(f"Refresh Request Failed: {error_message}")

    def refresh_semantic_model(self, expected_duration=30, wait_for_completion=True, loop_interval=10):
        """
        Initiates and optionally waits for the completion of a semantic model refresh.

        Parameters:
            expected_duration (int): Expected duration to wait before checking the status. Defaults to 30 seconds.
            wait_for_completion (bool): Whether to wait for the completion of the refresh. Defaults to True.
            loop_interval (int): Interval between status checks if waiting for completion. Defaults to 10 seconds.

        Returns:
            str: The status of the semantic model refresh or an error message.
        """
        try:
            # Sending a refresh request
            refresh_response = self._send_refresh_request()
            result = self._handle_refresh_trigger_response(refresh_response)
            
            # If not waiting for completion, return the initial result
            if not wait_for_completion:
                return result
            
            # Wait for the expected duration before checking the status
            time.sleep(expected_duration)
            
            # Loop to check the refresh status
            while True:
                refresh_status = self._get_refresh_status()
                result = self._handle_refresh_status_response(refresh_status)
                
                # Check the status of the refresh
                status = result["value"][0]["status"]
                if status != "Unknown":
                    print(f"Semantic model refresh completed with status: {status}")
                    return status
                
                print("Refresh is in progress. Waiting to check again...")
                time.sleep(loop_interval)
        except Exception as e:
            return str(e)






