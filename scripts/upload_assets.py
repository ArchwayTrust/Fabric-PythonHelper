import os
import requests

def upload_asset(upload_url, token, file_path):
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    # Construct the actual upload URL
    actual_url = upload_url.replace("{?name,label}", "") + f"?name={os.path.basename(file_path)}"

    with open(file_path, 'rb') as file:
        files = {
            "file": (os.path.basename(file_path), file, "application/octet-stream")
        }
        response = requests.post(actual_url, headers=headers, files=files)
        response.raise_for_status()

def main():
    token = os.environ['GITHUB_TOKEN']
    upload_url = os.environ['UPLOAD_URL']
    dist_path = 'dist'

    for filename in os.listdir(dist_path):
        file_path = os.path.join(dist_path, filename)
        if os.path.isfile(file_path):
            print(f"Uploading {file_path}...")
            upload_asset(upload_url, token, file_path)

if __name__ == "__main__":
    main()