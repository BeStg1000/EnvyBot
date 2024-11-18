import requests
import re

def validate_roblox_url(url):
    pattern = r"https://www.roblox.com/users/(\d+)/profile"
    return re.match(pattern, url)

def fetch_roblox_data(user_id):
    api_url = f"https://users.roblox.com/v1/users/{user_id}"
    response = requests.get(api_url)
    if response.status_code == 200:
        return response.json()
    return None
