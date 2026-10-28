from app.news_parser.sites import fetch_page, parse_all_news

url = "https://highload.tech/uk/tag/python-uk/"
html = fetch_page(url)

news_list = parse_all_news(html)

print("Знайдено новин:", len(news_list))

for news in news_list:
    print("\nЗаголовок:", news["title"])
    print("Текст:", news["text"])