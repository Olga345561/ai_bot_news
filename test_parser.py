from app.news_parser.sites import fetch_page, parse_all_news, parse_article
from bs4 import BeautifulSoup

url = "https://highload.tech/uk/tag/python-uk/"
html = fetch_page(url)

news_list = parse_all_news(html, "Highload")
soup = BeautifulSoup(html, "html.parser")
news_cards = soup.find_all("div", class_="lenta-item")

article_url = news_list[0]["url"]
article_html = fetch_page(article_url)
article = parse_article(article_html)
print(article["title"],
      article["text"])

article_html = fetch_page(article_url)
article_soup = BeautifulSoup(article_html, "html.parser")
news_data = {
    **news_list[0],
    "raw_text": article["text"]
}

print(news_data.keys())

content = article_soup.find("div", class_="content-inner")

if content:
    paragraphs = content.find_all("p")

    article_text = []

    for paragraph in paragraphs:
        text = paragraph.get_text(" ", strip=True)

        if text and not text.startswith("Підписуйтесь на нас"):
            article_text.append(text)

    full_text = "\n\n".join(article_text)

    print("Повний текст статті:")
    print(full_text)

else:
    print("Контейнер статті не знайдено")

for card in news_cards:
    if card.find("h2") and card.find("p", class_=None):
        print(card.prettify())
        break

article_tag = article_soup.find("article")

# if article_tag:
#     print(article_tag.prettify()[:5000])
# else:
#     print("Тег article не знайдено")
#
# for tag in article_soup.find_all(["div", "section", "article"]):
#     classes = tag.get("class")
#
#     if classes:
#         print(classes)

print("Назва сторінки статті:")
print(article_soup.title.get_text(strip=True))
print("Заголовок статті:")
print(article_soup.find("h1").get_text(strip=True))
print("Загальна кількість новин:", len(news_list))
print("Перша новина", news_list[0])


for number, news in enumerate(news_list, start=1):
    print(f"\nНовина №{number}")
    print("Заголовок:", news["title"])
    print("Посилання:", news["url"])
    print("Дата:", news["published_at"])

for number, news in enumerate(news_list[:3], start=1):
    article_html = fetch_page(news["url"])
    article = parse_article(article_html)

    print(f"\nНовина №{number}")
    print("Заголовок:", article["title"])
    print("Довжина тексту:", len(article["text"]))

