import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access the key
openai_key = os.getenv("OPENAI_API_KEY")

if not openai_key:
    print("Error: OPENAI_API_KEY not found. Please check your .env file.")
else:
    print("Successfully loaded API key!")