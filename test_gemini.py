import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if api_key:
    try:
        genai.configure(api_key=api_key)
        models = [m for m in genai.list_models()]
        for model in models:
            print(f"Model: {model.name}")
            print(f"  Description: {model.description}")
            print(f"  Supported Generation Methods: {model.supported_generation_methods}")
            print("-" * 20)
    except Exception as e:
        print(f"Error: {e}")
else:
    print("API Key not found.")