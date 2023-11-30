import requests
import json
import time

class SemanticModelRefresher:
    BASE_URL = "https://api.powerbi.com/v1.0/myorg/datasets/"

    def __init__(self, semantic_model_id, access_token, refresh_body={"notifyOption": "NoNotification"}):
        self.semantic_model_id = semantic_model_id
        self.access_token = access_token
        self.refresh_body = refresh_body

    def _send_refresh_request(self):
        refresh_endpoint = f"{self.BASE_URL}{self.semantic_model_id}/refreshes"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        response = requests.post(refresh_endpoint, headers=headers, json=self.refresh_body)
        response.raise_for_status()
        
        return response

    def _handle_refresh_trigger_response(self, response):
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

    def _get_refresh_status(self):
        refresh_endpoint = f"{self.BASE_URL}{self.semantic_model_id}/refreshes"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
        }

        response = requests.get(refresh_endpoint, headers=headers)
        response.raise_for_status()
        
        return response.json()

    def _handle_refresh_status_response(self, response):
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

    def refresh_semantic_model(self, expected_duration=30, wait_for_completion=True, loop_interval=10):
        try:
            refresh_response = self._send_refresh_request()
            result = self._handle_refresh_trigger_response(refresh_response)
            
            if not wait_for_completion:
                return result
            
            time.sleep(expected_duration)
            
            while True:
                refresh_status = self._get_refresh_status()
                result = self._handle_refresh_status_response(refresh_status)
                
                status = result["value"][0]["status"]
                if status != "Unknown":
                    print(f"Dataflow refresh completed with status: {status}")
                    return status
                
                print("Refresh is in progress. Waiting to check again...")
                time.sleep(loop_interval)
        except Exception as e:
            return str(e)





