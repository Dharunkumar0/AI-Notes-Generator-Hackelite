import requests
import json

# The URL for the image processing endpoint
url = 'http://localhost:8000/api/image/process'

# Get a JWT token (you'll need to replace this with a valid token)
token = input("Enter your JWT token: ")

# Headers including the authorization token
headers = {
    'Authorization': f'Bearer {token}'
}

# The image file to upload (replace with your image path)
image_path = input("Enter the path to your image file: ")

try:
    # Open and send the file
    with open(image_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(url, headers=headers, files=files)
    
    # Check the response
    if response.status_code == 200:
        print("Success!")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"Error: {str(e)}")
