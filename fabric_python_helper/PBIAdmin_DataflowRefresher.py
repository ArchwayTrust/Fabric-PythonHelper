import requests
import json
import time

class PBI_DataflowRefresher:
    BASE_URL = "https://api.powerbi.com/v1.0/myorg/groups/"

    def __init__(self, workspace_id, dataflow_id, access_token, refresh_body={"notifyOption": "NoNotification"}):
        self.workspace_id = workspace_id
        self.dataflow_id = dataflow_id
        self.access_token = access_token
        self.refresh_body = refresh_body

    def _send_refresh_request(self):
        refresh_endpoint = f"{self.BASE_URL}{self.workspace_id}/dataflows/{self.dataflow_id}/refreshes"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        response = requests.post(refresh_endpoint, headers=headers, json=self.refresh_body)
        response.raise_for_status()
        
        return response

    def _handle_refresh_response(self, response):
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
        transaction_endpoint = f"{self.BASE_URL}{self.workspace_id}/dataflows/{self.dataflow_id}/transactions"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
        }

        response = requests.get(transaction_endpoint, headers=headers)
        response.raise_for_status()
        
        return response.json()

    def _handle_transaction_response(self, response):
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
        try:
            refresh_response = self._send_refresh_request()
            result = self._handle_refresh_response(refresh_response)
            
            if not wait_for_completion:
                return result
            
            time.sleep(expected_duration)
            
            while True:
                transaction_status = self._get_transaction_status()
                result = self._handle_transaction_response(transaction_status)
                
                status = result['value'][0]['status']
                if status != "InProgress":
                    print(f"Dataflow refresh completed with status: {status}")
                    return status
                
                print("Refresh is in progress. Waiting to check again...")
                time.sleep(loop_interval)
        except Exception as e:
            return str(e)