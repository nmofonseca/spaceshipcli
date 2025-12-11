import requests
import os
from rich import print_json
from dotenv import load_dotenv  # Import the load_dotenv function

# Load environment variables from a .env file
# This line looks for a .env file in the current directory and loads its content
# into the environment, making them accessible via os.getenv()
load_dotenv()

url = "https://spaceship.dev/api/v1/domains?take=5&skip=0&orderBy=name"

# os.getenv will now find the variables loaded from your .env file.
api_key = os.getenv("SPACESHIP_API_KEY")
api_secret = os.getenv("SPACESHIP_API_SECRET")

# Check if the keys were found
if not api_key or not api_secret:
    print("Error: API key or secret not found.")
    print("Please make sure you have a .env file with SPACESHIP_API_KEY and SPACESHIP_API_SECRET.")
else:
    headers = {
        "X-API-Key": api_key,
        "X-API-Secret": api_secret
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # This will raise an exception for HTTP errors (4xx or 5xx)
        
        # Colorized and pretty-printed JSON response
        print_json(data=response.json())

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")