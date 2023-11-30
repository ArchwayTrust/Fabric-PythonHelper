import requests
import json
import time

class PBI_DataflowRefresher:
    # Base URL for Power BI API calls
    BASE_URL = "https://api.powerbi.com/v1.0/myorg/groups/"

    def __init__(self, workspace_id, dataflow_id, access_token, refresh_body={"notifyOption": "NoNotification"}):
        """
        Initializes the dataflow refresher instance with necessary parameters.

        Parameters:
            workspace_id (str): The ID of the Power BI workspace.
            dataflow_id (str): The ID of the Power BI dataflow.
            access_token (str): Access token for Power BI API authentication.
            refresh_body (dict): The request body for the refresh. Defaults to no notification.
        """
        self.workspace_id = workspace_id
        self.dataflow_id = dataflow_id
        self.access_token = access_token
        self.refresh_body = refresh_body

    def _send_refresh_request(self):
        """
        Sends a refresh request to the Power BI API for the specified dataflow.

        Returns:
            Response: The response object from the requests.post call.
        """
        # Constructing the refresh endpoint URL
        refresh_endpoint = f"{self.BASE_URL}{self.workspace_id}/dataflows/{self.dataflow_id}/refreshes"
        
        # Setting up the request headers
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        # Making a POST request to start the refresh
        response = requests.post(refresh_endpoint, headers=headers, json=self.refresh_body)
        response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
        
        return response

    def _handle_refresh_response(self, response):
        """
        Handles the response from the refresh request.

        Parameters:
            response (Response): The response object from the refresh request.

        Returns:
            str: The result of the refresh request handling.
        """
        if response.ok:
            print("Refresh requested successfully. Waiting for expected duration...")
            return "Refresh started"
        elif response.status_code == 404:
            error_message = "Resource Not Found. Check the WorkspaceId and DataflowId."
            print(error_message)
            raise Exception(f"Refresh Request Failed: {error_message}")
        else:
            error_message = f"Request failed with status code: {response.status_code}"
            print(error_message)
            raise Exception(f"Refresh Request Failed: {error_message}")

    def _get_transaction_status(self):
        """
        Gets the transaction status of the dataflow refresh.

        Returns:
            dict: The JSON response from the transaction status request.
        """
        # Constructing the transaction endpoint URL
        transaction_endpoint = f"{self.BASE_URL}{self.workspace_id}/dataflows/{self.dataflow_id}/transactions"
        
        # Setting up the request headers
        headers = {
            "Authorization": f"Bearer {self.access_token}",
        }

        # Making a GET request to retrieve the transaction status
        response = requests.get(transaction_endpoint, headers=headers)
        response.raise_for_status()
        
        return response.json()

    def _handle_transaction_response(self, response):
        """
        Handles the transaction response from the Power BI API.

        Parameters:
            response (Response): The response object from the transaction request.

        Returns:
            dict: The JSON response containing the transaction status.
        """
        try:
            if response.ok:
                return response.json()
            else:
                error_message = f"Transaction Request failed with status code: {response.status_code}"
                print(error_message)
                raise Exception(f"Refresh Request Failed: {error_message}")
        except json.JSONDecodeError:
            error_message = f"Invalid JSON response. Status Code: {response.status_code}. Response Text: {response.text}"
            print(error_message)
            raise Exception(f"Refresh Request Failed: {error_message}")

    def refresh_dataflow(self, expected_duration=30, wait_for_completion=True, loop_interval=10):
        """
        Initiates and optionally waits for the completion of a dataflow refresh.

        Parameters:
            expected_duration (int): Expected duration to wait before checking the status. Defaults to 30 seconds.
            wait_for_completion (bool): Whether to wait for the completion of the refresh. Defaults to True.
            loop_interval (int): Interval between status checks if waiting for completion. Defaults to 10 seconds.

        Returns:
            str: The status of the dataflow refresh or error message.
        """
        try:
            # Sending a refresh request
            refresh_response = self._send_refresh_request()
            result = self._handle_refresh_response(refresh_response)
            
            # If not waiting for completion, return the initial result
            if not wait_for_completion:
                return result
            
            # Wait for the expected duration before checking the status
            time.sleep(expected_duration)
            
            # Loop to check the transaction status
            while True:
                transaction_status = self._get_transaction_status()
                result = self._handle_transaction_response(transaction_status)
                
                # Check the status of the refresh
                status = result['value'][0]['status']
                if status != "InProgress":
                    print(f"Dataflow refresh completed with status: {status}")
                    return status
                
                print("Refresh is in progress. Waiting to check again...")
                time.sleep(loop_interval)
        except Exception as e:
            return str(e)