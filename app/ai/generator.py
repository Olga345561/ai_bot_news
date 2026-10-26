from app.ai.openai_client import client

def generate_post(title:str, text:str) ->str:
    response = client.chat.completions.create(
        model="gpt-5-nano",
        messages =[
            {
               "role":"system",
                "content":(
                    "Ти редактор Telegram-каналу. "
                    "Створи короткий, зрозумілий допис українською мовою "
                    "на основі наданої новини. "
                    "Збережи факти, не вигадуй інформацію. "
                    "Додай доречний заголовок та емодзі."
                )
            }, {
                "role":"user",
                "content":f"Заголовок: {title}\n\nТекст новини:\n{text}"
            }
        ]
    )
    generated_text = response.choices[0].message.content

    if not generated_text:
        raise ValueError("ШІ не повернув текст допису")
    return generated_text.strip()


