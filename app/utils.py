def matches_keywords(title: str, text:str, keywords: list[str]) -> bool:

    #Перевіряє, чи містить заголовок або текст новини
    #хоча б одне ключове слово.
    news_text = f"{title} {text}".casefold()

    for keyword in keywords:
        if keyword.casefold() in news_text:
            return True
    return False