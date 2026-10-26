import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("Не знайдено OPENAI_API_KEY у файлі .env")
client = OpenAI(api_key=api_key)