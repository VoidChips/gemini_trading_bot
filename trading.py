import os
from dotenv import load_dotenv

load_dotenv()

# get api credentials from environment variables
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

print(f"api key: {API_KEY}")
print(f"api secret: {API_SECRET}")
