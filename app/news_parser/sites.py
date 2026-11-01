import requests
from fastapi import HTTPException
from bs4 import BeautifulSoup

def parse_news(html:str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    # Знаходимо текст новини, за яким визначаємо картку
    news_text= soup.find(
        string=lambda text: text and "Розробники Python випустили версію 3.15" in text
    )

    if not news_text:
        return {"title":"",
                "text":"",}

    # Знаходимо картку конкретної новини
    news_card = news_text.find_parent(
        "div",
        class_="lenta-item")

    if not news_card:
        return {"title":"",
                "text":"",}

    # Витягуємо заголовок і текст
    title_tag = news_card.find("h2")
    text_tag = news_card.find("p", class_=None)
    title = title_tag.get_text(strip=True)if title_tag else ""
    text = text_tag.get_text(strip=True) if text_tag else ""
    return {"title":title,
            "text":text,}
#Одержуємо список всіх новин
def parse_all_news(html:str, source:str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    news_card = soup.find_all("div", class_="lenta-item")

    news_list = []

    for news in news_card:
        title_tag = news.find("h2")
        text_tag = news.find("p", class_=None)
        url_tag = title_tag.find_parent("a") if title_tag else None
        published_tag = news.find("span", class_="meta-datetime")

        title = title_tag.get_text(strip=True)if title_tag else ""
        text = text_tag.get_text(strip=True) if text_tag else ""
        url = url_tag.get("href") if url_tag else ""
        published_at = published_tag.get_text(strip=True) if published_tag else None
        if title and text:
            news_list.append({"title":title,
                              "summary":text,
                              "url":url,
                              "published_at":published_at,
                              "source":source})
    #     else:
    #         print("\nПропущена картка:")
    #         print(news.prettify())
    # print("Знайдено новин:", len(news_list))

    return news_list

#Завантажуємо HTML сторінки
def fetch_page(url: str) -> str:
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.exceptions.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Не вдалося отримати сторінку: {e}")
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=502, detail="Помилка під час запиту до сайту")

def fetch_and_parse_news(url:str) -> dict:
    html = fetch_page(url)
    news = parse_news(html)
    return news

#Витягує заголовок і повний текст статті
def parse_article(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    content = soup.find("div", class_="content-inner")

    if not content:
        return {"title": "", "text": ""}

    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else ""

    paragraphs = content.find_all("p")
    article_text = []

    for paragraph in paragraphs:
        text = paragraph.get_text(" ", strip=True)

        if text and not text.startswith("Підписуйтесь на нас"):
            article_text.append(text)

    full_text = "\n\n".join(article_text)

    return {
        "title": title,
        "text": full_text
    }