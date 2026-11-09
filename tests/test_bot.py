import os
import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("TELEGRAM_BOT_TOKEN")

response = requests.get(
    f"https://api.telegram.org/bot{token}/getMe",
    timeout=(5, 30)
)

print("HTTP:", response.status_code)
print("Відповідь:", response.json().get("ok"))
print("Опис:", response.json().get("description"))